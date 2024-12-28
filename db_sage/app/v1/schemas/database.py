from pydantic import BaseModel
from typing import Optional


class DatabaseConnection(BaseModel):
    """Database connection request schema"""

    host: str
    database_type: Optional[str] = "postgresql"
    username: str
    password: str
    database_name: str
    port: Optional[int] = 5432
