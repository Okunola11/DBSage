from pydantic import BaseModel

class Prompt(BaseModel):
    """Schema for user prompt"""

    prompt: str