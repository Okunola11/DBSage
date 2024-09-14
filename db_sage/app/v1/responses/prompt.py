from db_sage.app.core.base.responses import BaseResponse, BaseResponseData


class SqlQueryResponseData(BaseResponseData):
    """Schema for sql query data response"""

    prompt: str
    results: list
    sql: str

class SqlQueryResultsResponse(BaseResponse):
    """Schema for sql query response"""

    data: SqlQueryResponseData