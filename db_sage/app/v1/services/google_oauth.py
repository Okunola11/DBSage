from fastapi import Depends, HTTPException, status, Response
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from typing import Annotated, Union

from db_sage.app.db.database import get_db
from db_sage.app.v1.models.user import User, UserToken
from db_sage.app.v1.models.oauth import OAuth
from db_sage.app.core.base.services import Service
from db_sage.app.utils.logger import logger
from db_sage.app.v1.services.user import user_service
from db_sage.app.v1.responses.user import UserResponseData, UserLoginResponse


class GoogleOAuthService(Service):
    """Handles database operations for Google OAuth

    Args:
        Service (cls): A class with abstract methods for services
    """
    def create(self, google_response: dict, db: Annotated[Session, Depends(get_db)]) -> object:
        """Create a user using information gotten from google 

        Args:
            google_response (dict): The raw data from google oauth2
            db (Annotated[Session, Depends): Database session to manage the database operations 

        Returns:
            object: A new user object 
        """
        try:
            # check for the user info from google auth 
            user_info: dict = google_response.get("userinfo")

            existing_user = db.query(User).filter_by(email=user_info.get("email")).one_or_none()

            if existing_user: 
                print(f"Existing user  is {existing_user}")
                # retrieve the user's google_access_token 
                oauth_data = db.query(OAuth).filter_by(user_id=existing_user.id).one_or_none()
                # if it exists
                if oauth_data:
                    print("OAuth data already exists")
                    self.update(oauth_data, google_response, db)
                    # pass the existing user to the get_response method to generate a response object 
                    user_response = self.get_response(existing_user, db)
                    # return the response
                    return user_response
                else:
                    try:
                        print(f"OAuth data doesn't exist \n")
                        print(f"Generating new oauth data")
                        # user login through google oauth for the first time
                        oauth_data = OAuth(
                            user_id=existing_user.id,
                            provider="google",
                            sub=user_info.get("sub"),
                            access_token=google_response.get("access_token", ""),
                            refresh_token=google_response.get("refresh_token", "")
                        )
                        # add and commit to get the inserted_id
                        db.add(oauth_data)
                        db.commit()
                        # update the user's relationship with oauth
                        existing_user.oauth = oauth_data
                        existing_user.update_at = datetime.now(timezone.utc)
                        db.commit()
                        # pass the user object to get_response method to generate a response object 
                        user_response = self.get_response(existing_user, db)
                        # return the response
                        return user_response
                    except Exception as exc:
                        db.rollback()
                        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception occured in oauth creation; {exc}")
            else:
                try:
                    # if user is not in database, we create a new user using the oauth_data
                    # link the user to the associated oauth_data
                    print(f"Creating new USER")
                    new_user = User(
                        first_name=user_info.get("given_name"),
                        last_name=user_info.get("family_name"),
                        email=user_info.get("email"),
                        is_active=True,
                        is_verified=True,
                        updated_at=datetime.now(timezone.utc),
                        verified_at=datetime.now(timezone.utc)
                    )
                    # commit to get the user_id
                    db.add(new_user)
                    db.commit()

                    print(f"GOOGLE ACCESS TOKEN IS {google_response.get('access_token')}")
                    # oauth data 
                    oauth_data = OAuth(
                        user_id=new_user.id,
                        provider="google",
                        sub=user_info.get("sub"),
                        access_token=google_response.get("access_token", ""),
                        refresh_token=google_response.get("refresh_token", "")
                    )
                    # add and commit to get the inserted_id
                    # add the profile url for the user_info dict
                    # profile = Profile(
                    #     user_id=new_user.id,
                    #     avatar_url=user_info.get("picture")
                    # )

                    # commit to database
                    # db.add_all([oauth_data, profile])
                    db.add(oauth_data)
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception occured in user creation; {exc}")

                db.refresh(new_user)

                # pass the user object to the get_response model to get a response
                user_response = self.get_response(new_user, db)
                # return the user response
                return user_response

        except Exception as exc: 
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception occured in create method; {exc}")
       
    def fetch(self):
        """Fetch method
        """

    def fetch_all(self):
        pass

    def delete(self):
        """Delete method
        """

    def update(self, oauth_data: object, google_response: dict, db: Annotated[Session, Depends(get_db)]) -> None:
        """Updates a users information in the OAuth table

        Args:
            oauth_data (object): the oauth object of the user
            google_response (dict): the response data from google oauth
            db (Annotated[Session, Depends): the database session object for connection 
        """
        try:
            # update the access and refresh token 
            oauth_data.access_token = google_response.get("access_token", "")
            oauth_data.refresh_token = google_response.get("refresh_token", "")
            oauth_data.updated_at = datetime.now(timezone.utc)
            # commit and return the user object 
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception occured in update method; {exc}")

    def get_response(self, user: object, db: Annotated[Session, Depends(get_db)]) -> object:
        """Creates a response for the end user 

        Args:
            user (object): the user object 

        Returns:
            object: the response object for the end user 
        """

        try:
            # check if the user has existing tokens that are yet to expire
            existing_token = db.query(UserToken).filter(
                UserToken.user_id == user.id, 
                UserToken.expires_at > datetime.utcnow()
                ).first()

            if existing_token:
                existing_token.expires_at = datetime.utcnow()
                db.add(existing_token)
                db.commit()

            tokens = user_service._generate_tokens(user, db)

            user_data = UserResponseData.model_validate(user)

            pydantic_model = UserLoginResponse(
                message="Login successful",
                access_token=tokens['access_token'],
                expires_in=tokens['expires_in'],
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
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Exception occured in get_response method; {exc}")
