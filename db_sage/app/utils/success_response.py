from typing import Optional
from fastapi.responses import JSONResponse

def success_response(status_code: int = 200, message: str = "", data: Optional[dict] = None) -> dict:
    """Success response model

    Args:
        - status_code (int): The status code to be returned
        - message (str): Success message to be sent
        - data (Optional[dict], optional): Data to be returned if availbale. Defaults to None.

    Returns:
        dict: response data
    """
    
    response_data = {
        "status_code": status_code,
        "success": True,
        "message": message,
    }

    if data:
        response_data['data'] = data

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )