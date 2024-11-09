import uvicorn
import asyncio
from fastapi import FastAPI, status, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware # required by google oauth
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from db_sage.app.utils.settings import settings
from db_sage.app.utils.logger import logger
from db_sage.app.v1.routes import api_version_one
from db_sage.app.core.config.db import DatabaseStateManager

@asynccontextmanager
async def lifespan(app: FastAPI):
     # Startup
    print("Starting up application...")
    cleanup_task = None
    
    try:
        # Initialize periodic cleanup
        from fastapi_utils.tasks import repeat_every
        
        @repeat_every(seconds=3600)
        async def cleanup_old_connections():
            print("Running periodic connection cleanup...")
            DatabaseStateManager().cleanup_inactive_connections()
        
        # Start the cleanup task
        cleanup_task = asyncio.create_task(cleanup_old_connections())
        
        yield
        
    finally:
        # Shutdown
        print("Shutting down application...")
        
        # Cancel cleanup task if it exists
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all database connections
        db_state = DatabaseStateManager()
        connections = list(db_state._connections.keys())
        if connections:
            print(f"Closing {len(connections)} database connections...")
            for user_id in connections:
                db_state.close_connection(user_id)

app = FastAPI(
    lifespan=lifespan,
    title="DBSage",
    description="Talk to your SQL database",
    version="1.0.0"
)

# Create a limiter instance
limiter = Limiter(key_func=get_remote_address)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

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
            "success": False,
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
            "success": False,
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
            "success": False,
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
            "success": False,
            "status_code": 500,
            "messasge": f"An unexpected error occured; {exc}"
        }
    )

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "status_code": 429,
            "message": "Slow down, you are making too many requests"
        }
    )


def main():
    return uvicorn.run("db_sage.main:app", port=8000, reload=True)

if __name__ == "__main__":
    main()
