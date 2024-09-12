from pydantic import BaseModel, ConfigDict
from typing import Any, Optional

class BaseResponseData(BaseModel):
    """Base schema for response data"""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class BaseResponse(BaseModel):
    """Base schema for all responses"""

    status_code: int = 200
    message: str
    data: Optional[Any] = {}