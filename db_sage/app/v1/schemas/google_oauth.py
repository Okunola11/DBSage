from pydantic import BaseModel, Field

from db_sage.app.v1.responses.user import UserResponseData


class OAuthToken(BaseModel):
    id_token: str


class GoogleLoginTokenRequest(BaseModel):
    """Request schema for google login token"""

    token: str = Field(examples=["ljjf0939jlfjkfj"])


class GoogleLoginTokenResponse(BaseModel):
    """
    Response model for token response after google authorization
    """

    success: bool = Field(default=True, examples=[True])
    status_code: int = Field(default=200, examples=[200])
    message: str = Field(
        default="Google login successful", examples=["Google login successful"]
    )
    access_token: str = Field(examples=["some_jwt_token"])
    expires_in: int = Field(examples=[60])
    data: UserResponseData
