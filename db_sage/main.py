import uvicorn
from fastapi import FastAPI, status, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware # required by google oauth

from db_sage.app.utils.settings import settings
from db_sage.app.utils.logger import logger
from db_sage.app.v1.routes import api_version_one

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(api_version_one)

@app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Welcome to API"
        }
    )

# EXCEPTION HANDLERS
@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    """HTTP Exception Handler

    Returns a standardized json response for raised http exceptions 

    Args:
        request (Request): the request object
        exc (HTTPException): the exception raised
    """

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    """Request validation exception handler

    Args:
        request (Request): the request object
        exc (RequestValidationError): the exception raised

    Returns:
        dict: formatted error details of all errors
    """

    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={
            "status": False,
            "status_code": 422,
            "message": "Invalid input",
            "errors": errors
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    """Sqlalchemy integrity error handler"""

    logger.exception(f"Exception occured; {exc}")

    return JSONResponse(
        status_code=400,
        content={
            "status": False,
            "status_code": 400,
            "message": f"An unexpected error occured; {exc}"
        }
    )

@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    """Other exception handler"""

    logger.exception(f"Exception occured; {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "messasge": f"An unexpected error occured; {exc}"
        }
    )


def main():
    return uvicorn.run("db_sage.main:app", port=8000, reload=True)

if __name__ == "__main__":
    main()
