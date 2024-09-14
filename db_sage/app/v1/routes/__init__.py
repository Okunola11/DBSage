from fastapi import APIRouter
from db_sage.app.v1.routes.google_auth import google_auth
from db_sage.app.v1.routes.auth import auth
from db_sage.app.v1.routes.user import user_router
from db_sage.app.v1.routes.prompt import prompt_router

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(google_auth)
api_version_one.include_router(user_router)
api_version_one.include_router(prompt_router)