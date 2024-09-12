from typing import Union
from typing_extensions import List
from datetime import datetime
from pydantic import EmailStr

from db_sage.app.core.base.responses import BaseResponse, BaseResponseData

class UserResponseData(BaseResponseData):
    """Schema for get user data response"""

    id: str
    email: EmailStr
    last_name: str
    first_name: str
    is_active: bool = False
    is_verified: bool = False
    is_superadmin: bool = False
    created_at: Union[str, None, datetime] = None

class RegisterUserResponse(BaseResponse):
    """Schema for register user response"""

    status_code: int = 201
    access_token: str
    data: UserResponseData

class UserLoginResponse(BaseResponse):
    """Schema for user login response"""

    access_token: str
    data: UserResponseData

class RefreshTokenResponse(BaseResponse):
    """Schema for token refresh response"""

    access_token: str

class SuperAdminUserResponseData(BaseResponseData):
    """Schema for super admin fetch user data"""

    id: str
    email: EmailStr
    last_name: str
    first_name: str
    is_active: bool = True  
    is_deleted: bool = False
    is_verified: bool = False
    is_superadmin: bool = False
    created_at: Union[str, None, datetime] = None
    updated_at: Union[str, None, datetime] = None
    verified_at: Union[str, None, datetime] = None

class SuperAdminFetchUserResponse(BaseResponse):
    """Schema for super admin fetch user response"""

    data: SuperAdminUserResponseData

class FetchUserResponse(BaseResponse):
    """Schema for super admin fetch user response"""

    data: UserResponseData

class FetchAllUsersResponse(BaseResponse):
    """Schema for super admin fetch all users respone"""

    page: int = 1
    per_page: int = 10
    total: int = 0
    data: List[SuperAdminUserResponseData]