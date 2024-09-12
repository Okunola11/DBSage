from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Any

from db_sage.app.v1.models.user import User, UserToken
from db_sage.app.core.base.services import Service
from db_sage.app.utils.email_context import FORGOT_PASSWORD, USER_VERIFY_ACCOUNT
from db_sage.app.utils.settings import settings
from db_sage.app.utils.logger import logger
from db_sage.app.utils.string import unique_string
from db_sage.app.utils.db_validators import check_model_existence
from db_sage.app.core.config.security import (
    hash_password, verify_password, str_encode, str_decode, generate_token,
    load_user, get_token_payload
    )
from db_sage.app.v1.services.email import (
    account_verification_email, 
    account_activation_confirmation_email, 
    password_reset_email
    )
from db_sage.app.v1.responses.user import (
    UserResponseData, RegisterUserResponse, UserLoginResponse, FetchUserResponse,
    RefreshTokenResponse, SuperAdminFetchUserResponse, SuperAdminUserResponseData,
    FetchAllUsersResponse
    )
from db_sage.app.utils.success_response import success_response

class UserService(Service):
    async def create(self, data, db: Session, background_tasks):
        """Registers a new user

        Args:
            - data: the request data
            - db: the databases session
            - background_tasks: background task to be called for email service

        Raises:
            - HTTPException: 400 if the email in the request data already exists in the database
            - HTTPException: 500 if any other error occurs

        Returns:
            dict: a user response object containing auth tokens and the users data
        """

        user_exist = db.query(User).filter_by(email = data.email).first()
        if user_exist:
            raise HTTPException(status_code=400, detail="Email already exists")
        try:
            data.password = hash_password(data.password)
            user = User(**data.model_dump())
            db.add(user)
            db.commit()
            db.refresh(user)

            # generating auth tokens
            tokens = self._generate_tokens(user, db)

            # Account verification email 
            await account_verification_email.send(user, background_tasks)

            user_data = UserResponseData.model_validate(user)

            pydantic_model = RegisterUserResponse(
                message=f"User {user.email} created successfully",
                access_token=tokens['access_token'],
                data=user_data
            )

            # create a response object
            response = Response(
                content=pydantic_model.json(), status_code=status.HTTP_201_CREATED, media_type='application/json'
                )

            # sending the refresh token as a cookie
            response.set_cookie(
                key="refresh_token",
                value=tokens['refresh_token'],
                expires=timedelta(days=30),
                httponly=True,
                secure=True,
                samesite="none"
            )
            return response
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error {exc}")

    def fetch(self, db: Session, id):
        """Fetches all data of a single user

        Args:
            - db: the database session
            - id: unique id of the user to fetch

        Raises:
            - HTTPException: 404 for non-existing request id
            - HTTPException: 500 for any other error

        Returns:
            dict: the user object
        """

        user = check_model_existence(db, User, id)

        user_data = SuperAdminUserResponseData.model_validate(user)

        response = SuperAdminFetchUserResponse(
            message="Successfully fetched user",
            data=user_data
        )
        return response

    def fetch_me(self, user: User):
        """Fetch the current authenticated users details

        Args:
            user: the current user obj

        Returns:
            dict: success response with the current user obj
        """

        user_data = UserResponseData.model_validate(user)

        response = FetchUserResponse(
            message="Successfully fetched user",
            data=user_data
        )
        return response


    def fetch_all(self, db: Session, page: int, per_page: int, **query_params: Optional[Any]):

        # Creating filters for the query
        filters = []
        for key, value in query_params.items():
            if (value is not None) and (not isinstance(value, bool)):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                    detail=f"Invalid value for '{key}'. Must be a boolean" 
                    )

            # create the query condition
            if hasattr(User, key) and value is not None:
                filters.append(getattr(User, key) == value)
        
        offset_value = (page - 1) * per_page
        users = db.query(User).filter(*filters).limit(per_page).offset(offset_value).all()

        total_users = len(users)
        if total_users:
            all_user_data = [SuperAdminUserResponseData.model_validate(user, from_attributes=True) for user in users]

            response = FetchAllUsersResponse(
                message="Successfully fetched all users",
                page=page,
                per_page=per_page,
                total=total_users,
                data=all_user_data
            )
            return response
        response = FetchAllUsersResponse(
            message="No User(s) found",
            page=page,
            per_page=per_page,
            total=0,
            data=[]
        )
        return response
        

    def update(self, db: Session, current_user: User, data, id: Annotated[str, Optional] = None):
        """Updates a single user

        Args:
            - db: the database session
            - current_user: the current authenticated user
            - data: the update request data
            - id: request id. Defaults to None.

        Raises:
            - HTTPException: 400 for already existing request email
            - HTTPException: 404 for non existing user
            - HTTPException: 400 for deleted user
            - HTTPException: 400 for inactive user
            - HTTPException: 400 for unverified user
            - HTTPException: 400 for request id which doesn't belong to current user who is not a superadmin

        Returns:
            dict: updated user obj
        """

        if (not id) or (id and current_user.id == id) or current_user.is_superadmin:
            # check for existing email
            existing_email = db.query(User).filter_by(email=data.email).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already taken")

            user = current_user
            if (id and current_user.is_superadmin):
                user = check_model_existence(db, User, id)

            # check if user is deleted, inactive or unverified
            if user.is_deleted:
                raise HTTPException(status_code=400, detail="User is deleted and cannot be updated")

            if not user.is_verified:
                raise HTTPException(status_code=400, detail="User is not verified and cannot be updated")

            if not user.is_active:
                raise HTTPException(status_code=400, detail="User is inactive and cannot be updated")

            update_data = data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)
            db.commit()
            db.refresh(user)

            user_data = UserResponseData.model_validate(user)

            response = FetchUserResponse(
                message="User updated successfully",
                data=user_data
            )
            return response
        raise HTTPException(status_code=400, detail="Invalid request!")

    def delete(self, db: Session, current_user: User, id: str):
        """Soft delete a user

        Args:
            - db: the database session
            - current_user: the current authenticated superadmin
            - id: the ID of the user to delete

        Raises:
            - HTTPException: 409 for already deleted users
            - HTTPException: 400 for requests by non superadmin whose request ID do not match their ID
        """

        if current_user.is_superadmin:
            user = check_model_existence(db, User, id)

            # check if user is deleted
            if user.is_deleted:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already deleted")

            # soft delete user
            user.is_active = False
            user.is_deleted = True
            user.deleted_at = datetime.now(timezone.utc)
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request!")

    async def activate_user_account(self, data, db: Session, background_tasks):
        """Verifies a registered user

        Args:
            - data (dict): the request data (email and token) for verification
            - db: the database session
            - background_tasks: background task to be called for email service.

        Raises:
            - HTTPException: 400 if the request email doesn't exist
            - HTTPException:400 if the request token is not valid
            - HTTPException: 500 if the database operation fails 

        Returns:
            dict: a success response message
        """

        user = db.query(User).filter_by(email = data.email).first()
        if not user:
            raise HTTPException(status_code=400, detail="This link is not valid")
        
        user_token = user.get_context_string(context=USER_VERIFY_ACCOUNT)
        try:
            token_valid = verify_password(user_token, data.token)
        except Exception as verify_exc:
            logger.exception(verify_exc)
            token_valid = False
        if not token_valid:
            raise HTTPException(status_code=400, detail="This link is either expired or not valid")

        try:
            user.is_active = True
            user.is_verified = True
            user.updated_at = datetime.utcnow()
            user.verified_at = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error {exc}")

        # Activation confirmation Email
        await account_activation_confirmation_email.send(user, background_tasks)
        return success_response(
            status_code=200,
            message=f"User {user.email} account successfully activated."
        )


    async def get_login_token(self, data, db: Session):
        """Generated authentication tokens for users upon login

        Args:
            - data: request username and password
            - db: the database session

        Raises:
            - HTTPException: 400 for non-existing email
            - HTTPException: 400 for wrong username or password
            - HTTPException: 400 for non verified users
            - HTTPException: 400 for inactive users

        Returns:
            dict: the user data with tokens
        """

        user = await load_user(data.email, db)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid request!")

        if not verify_password(data.password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if not user.verified_at:
            raise HTTPException(status_code=400, detail="Your account is not verified. Please check your email inbox to verify your account.")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Your account has been deactivated. Please contact support.")

        # check if the user has existing tokens that are yet to expire
        existing_token = db.query(UserToken).filter(
            UserToken.user_id == user.id, 
            UserToken.expires_at > datetime.utcnow()
            ).first()

        if existing_token:
            existing_token.expires_at = datetime.utcnow()
            db.add(existing_token)
            db.commit()

        tokens = self._generate_tokens(user, db)

        user_data = UserResponseData.model_validate(user)

        pydantic_model = UserLoginResponse(
            message="Login successful",
            access_token=tokens['access_token'],
            data=user_data
        )

        # create a response object
        response = Response(
            content=pydantic_model.json(), status_code=status.HTTP_200_OK, media_type='application/json'
            )

        response.set_cookie(
            key="refresh_token",
            value=tokens['refresh_token'],
            expires=timedelta(days=30),
            httponly=True,
            secure=True,
            samesite="none"
        )
        return response


    async def get_refresh_token(self, refresh_token: str, db: Session):
        """Refreshes access token

        Args:
            - refresh_token: the request refresh token
            - db: the database session

        Raises:
            - HTTPException: 400 for absent request refresh token
            - HTTPException: 400 for invalid request refresh token

        Returns:
            dict: response message with new tokens
        """

        token_payload = get_token_payload(refresh_token, settings.SECRET_KEY, settings.ALGORITHM)
        if not token_payload:
            raise HTTPException(status_code=400, detail="Invalid request.")
        
        refresh_key = token_payload.get('t')
        access_key = token_payload.get('a')
        user_id = str_decode(token_payload.get('sub'))
        user_token = db.query(UserToken).options(joinedload(UserToken.user)).filter(
            UserToken.refresh_key == refresh_key,
            UserToken.access_key == access_key,
            UserToken.user_id == user_id,
            UserToken.expires_at > datetime.utcnow()
        ).first()

        if not user_token:
            raise HTTPException(status_code=400, detail="Invalid request.")

        user_token.expires_at = datetime.utcnow()
        db.add(user_token)
        db.commit()

        # generate new tokens
        tokens = self._generate_tokens(user_token.user, db)

        pydantic_model = RefreshTokenResponse(
            message="Refresh successful",
            access_token=tokens['access_token'],
        )

        # create a response object
        response = Response(
            content=pydantic_model.json(), status_code=status.HTTP_200_OK, media_type='application/json'
            )

        response.set_cookie(
            key="refresh_token",
            value=tokens['refresh_token'],
            expires=timedelta(days=30),
            httponly=True,
            secure=True,
            samesite="none"
        )
        return response
        

    def _generate_tokens(self, user: User, db: Session):
        """Generates access and refresh tokens

        Args:
            user: the user to be signed with the token
            db: the database session

        Returns:
            dict: access and refresh tokens
        """

        refresh_key = unique_string(100)
        access_key = unique_string(50)
        rt_expires = timedelta(minutes=15)
        # rt_expires = timedelta(days=settings.JWT_REFRESH_EXPIRY)

        user_token = UserToken(
            user_id = user.id,
            refresh_key = refresh_key,
            access_key = access_key,
            expires_at = datetime.utcnow() + rt_expires
        )
        db.add(user_token)
        db.commit()
        db.refresh(user_token)

        access_token_payload = {
            "sub": str_encode(user.id),
            "a": access_key,
            "r": str_encode(user_token.id),
            "n": str_encode(f"{user.last_name}")
        }
        
        at_expires = timedelta(minutes=5)
        # at_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = generate_token(access_token_payload, settings.SECRET_KEY, settings.ALGORITHM, at_expires)

        refresh_token_payload = {
            "sub": str_encode(user.id),
            "t": refresh_key,
            "a": access_key
        }
        refresh_token = generate_token(refresh_token_payload, settings.SECRET_KEY, settings.ALGORITHM, rt_expires)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": at_expires.seconds
        }

    async def email_forgot_password_link(self, data, background_tasks, db):
        """Sends password reset request mail to user

        Args:
            - data: the request data (email)
            - background_tasks: background task for email service
            - db: the database session

        Raises:
            - HTTPException: 400 for unverified users
            - HTTPException: 400 for inactive users
            - HTTPException: 500 for any other errors

        Returns:
            - dict: success message prompting the user to check their mail
        """

        user = await load_user(data.email, db)
        if user:
            if not user.verified_at:
                raise HTTPException(status_code=400, detail="Your account is not verified. Please check your email inbox to verify your account.")

            if not user.is_active:
                raise HTTPException(status_code=400, detail="Your account has been deactivated. Please contact support.")

            await password_reset_email.send(user, background_tasks)

        return success_response(
            status_code=200,
            message="Please check your mail to change password"
        )

    async def reset_user_password(self, data, db: Session):
        """Resets a users password

        Args:
            - data: the request data
            - db: the database session

        Raises:
            - HTTPException: 400 for non-existing user
            - HTTPException: 400 for unverified user
            - HTTPException: 400 for inactive user
            - HTTPException: 400 for invalid request token
            - HTTPException: 500 for any other errors

        Returns:
            - dict: success message
        """

        user = await load_user(data.email, db)

        if not user:
            raise HTTPException(status_code=400, detail="Invalid request")   

        if not user.verified_at:
            raise HTTPException(status_code=400, detail="Invalid request")  

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Invalid request")

        user_token = user.get_context_string(context=FORGOT_PASSWORD)

        try:
            token_valid = verify_password(user_token, data.token)
        except Exception as exc:
            logger.exception(exc)
            token_valid = False

        if not token_valid:
            raise HTTPException(status_code=400, detail="Invalid window")

        user.password = hash_password(data.password)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Notify user that the password has been updated through mail

        return success_response(
            status_code=200,
            message="Your password has been updated."
        )

user_service = UserService()