from db_sage.app.core.base.responses import BaseResponse, BaseResponseData
from typing import List


class SqlQueryResponseData(BaseResponseData):
    """Schema for sql query data response"""

    prompt: str
    table_context: List[str]
    sql: str
    csv_data: str  

class SqlQueryResultsResponse(BaseResponse):
    """Schema for sql query response"""

    data: SqlQueryResponseData