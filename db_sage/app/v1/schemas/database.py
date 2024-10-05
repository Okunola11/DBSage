from pydantic import BaseModel

class DatabaseUrl(BaseModel):
    """Schema for database connection request"""

    db_url: str