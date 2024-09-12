from pydantic_settings import BaseSettings
from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    """class to hold config values

    Args:
        BaseSettings
    """
    APP_NAME: str = config("APP_NAME")

    # Database configurations
    DB_HOST:str = config("DB_HOST")
    DB_PORT: int = config("DB_PORT", cast=int)
    DB_USER: str = config("DB_USER")
    DB_PASSWORD: str = config("DB_PASSWORD")
    DB_NAME: str = config("DB_NAME")
    DB_TYPE: str = config("DB_TYPE")

    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_EXPIRY: int = config("JWT_REFRESH_EXPIRY")

    MAIL_USERNAME: str = config("MAIL_USERNAME")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD")
    MAIL_PORT: int = config("MAIL_PORT", default=1025)
    MAIL_SERVER: str = config("MAIL_SERVER", default="smtp")
    MAIL_FROM: str = config("MAIL_FROM", default="noreply@test.com")
    MAIL_FROM_NAME: str = config("MAIL_FROM_NAME")

    FRONTEND_URL: str = config("FRONTEND_URL", default="http:localhost:3000")

settings = Settings()