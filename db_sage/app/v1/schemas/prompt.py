import re
from pydantic import BaseModel, model_validator


class Prompt(BaseModel):
    """Schema for user prompt"""

    prompt: str

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values: dict):
        """
        Validates fields.
        """
        prompt: str = values.get("prompt", "")

        if prompt:
            validate_fields(prompt, "prompt")
            validate_query(prompt, "prompt")
        return values


def validate_fields(name: str, field: str) -> None:
    """
    Validates user input that goes to the database against offensive or improper words
    """
    # offensive words
    offensive_words = [
        "fuck",
        "ass",
        "pussy",
        "asshole",
        "niggar",
        "bitch",
        "hoe",
        "cum",
        "scum",
        "bastard",
    ]

    offensive_regex = r"\b(?:" + "|".join(offensive_words) + r")\b"
    # check for offfensive words
    if re.search(offensive_regex, name.lower()):
        raise ValueError(f"{field} contains offensive language")


def validate_query(name: str, field: str) -> None:
    """
    Validates user prompt input
        - Only read requests are allowed
    """

    # Non read operations
    non_read_operations = [
        # Insert operations
        "insert",
        "add",
        "create",
        "new",
        # Update operations
        "update",
        "modify",
        "change",
        "alter",
        "edit",
        "set",
        "put",
        # Delete operations
        "delete",
        "remove",
        "drop",
        "truncate",
        "erase",
        # Data Manipulation Language (DML) keywords
        "merge",
        "replace",
        # Database/Table Modification
        "create table",
        "alter table",
        "rename",
        "grant",
        "revoke",
        # Destructive operations
        "destroy",
        "purge",
        "clear",
        # Specific SQL keywords indicating modification
        "into",
        "values",
        "set",
        "where",
    ]

    non_read_regex = r"\b(?:" + "|".join(non_read_operations) + r")\b"
    # check for non read operations
    if re.search(non_read_regex, name.lower()):
        raise ValueError(f"{field} contains non read operations")
