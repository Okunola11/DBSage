from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserData(BaseModel):
    """
    Schema response for validated google login
    """
    id: str
    first_name: str
    last_name: str 
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Tokens(BaseModel):
    """
    Schema for generated tokens response
    """
    access_token: str
    refresh_token: str
    token_type: str

class StatusResponse(BaseModel):
    """
    Response schema for the end user 
    """
    message: str
    status: str
    status_code: int = 200
    tokens: Tokens
    user: UserData
