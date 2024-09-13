import jwt
import base64
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload

from db_sage.app.v1.models.user import UserToken
from db_sage.app.utils.settings import settings
from db_sage.app.utils.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    """Function to hash password"""

    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifies a hashed password

    Args:
        plain_password (str): the plain input password
        hashed_password (str): the hashed password

    Returns:
        bool: true if they are a match, false otherwise
    """

    return pwd_context.verify(plain_password, hashed_password)

def str_encode(string: str) -> str:
    """Encodes a string

    Args:
        string (str): the string to encode

    Returns:
        str: the encoded string
    """

    return base64.b85encode(string.encode('ascii')).decode('ascii')

def str_decode(string: str) -> str:
    """Decodes a string

    Args:
        string (str): the string to decode

    Returns:
        str: the decoded string
    """

    return base64.b85decode(string.encode('ascii')).decode('ascii')

def generate_token(payload: dict, secret: str, algo: str, expiry: timedelta):
    """Generated a jwt token

    Args:
        - payload (dict): the payload data to encode in the token
        - secret (str): the token secret key
        - algo (str): the token algorithm
        - expiry (timedelta): the expirty time of the token

    Returns:
        str: an encoded token
    """

    expire = datetime.utcnow() + expiry
    payload.update({"exp": expire})
    return jwt.encode(payload, secret, algorithm=algo)

def get_token_payload(token: str, secret: str, algo: str):
    """Retrieves a token payload

    Args:
        - token: the jwt token
        - secret: the secret key associated with the token
        - algo (str): the token algorithm

    Returns:
       dict | none: the token payload or none
    """

    try:
        payload = jwt.decode(token, secret, algorithms=algo)
    except Exception as jwt_exec:
        logger.debug(f"JWT Error: {str(jwt_exec)}")
        payload = None
    return payload

async def get_token_user(token: str, db: Session):
    """Retrieves the user associated with a token

    Args:
        - token: the jwt token to retrieve the user from
        - db: the database session

    Returns:
        dict | none: the user object if the user exists or none if not
    """
    payload = get_token_payload(token, settings.SECRET_KEY, settings.ALGORITHM)
    if payload:
        user_token_id = str_decode(payload.get('r'))
        user_id = str_decode(payload.get('sub'))
        access_key = payload.get('a')

        user_token = db.query(UserToken).options(joinedload(UserToken.user)).filter(
            UserToken.access_key == access_key,
            UserToken.id == user_token_id,
            UserToken.user_id == user_id,
            UserToken.expires_at > datetime.utcnow()
        ).first()

        if user_token:
            return user_token.user
    return None

async def load_user(email: str, db: Session):
    """Gets a user by email

    Args:
        - email: the email of the user
        - db: the database session

    Returns:
        dict | none: the user obj if the user exists or none
    """

    from db_sage.app.v1.models.user import User
    try:
        user = db.query(User).filter_by(email = email).first()
    except Exception as user_exec:
        logger.info(f"User Not Found, Email: {email}")
        user = None
    return user    