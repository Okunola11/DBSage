from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from db_sage.app.db.database import get_db
from db_sage.app.core.dependencies.user import get_current_active_user
from db_sage.app.v1.schemas.prompt import Prompt
from db_sage.app.v1.responses.prompt import SqlQueryResultsResponse
from db_sage.app.v1.services.prompt import prompt_service

prompt_router = APIRouter(prefix="/prompt", tags=["Prompt"])

@prompt_router.post("", status_code=status.HTTP_200_OK, response_model=SqlQueryResultsResponse)
async def get_sql_query_from_prompt(
    data: Prompt,
    # user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Handles the HTTP POST request to generate and execute an SQL query based on the provided prompt.

    This endpoint receives a prompt from the client, utilizes the `PromptService` to generate and run the SQL query, and returns the results in the response.

    Args:
        data (Prompt): The prompt data containing the SQL query requirements.
        user (User): The currently authenticated user.

    Returns:
        SqlQueryResultsResponse: The response model containing:
            - A message indicating the success of the SQL query generation.
            - An instance of `SqlQueryResponseData` with:
                - `prompt`: The original prompt provided.
                - `results`: The results of the SQL query execution.
                - `sql`: The SQL query that was generated and executed.
    """

    return prompt_service.generate_and_run_sql(data)
