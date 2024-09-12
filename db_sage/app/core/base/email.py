from fastapi import BackgroundTasks

from db_sage.app.v1.models.user import User
from db_sage.app.core.config.email import send_email
from db_sage.app.utils.settings import settings

class BaseEmailSender:
    def __init__(self):
        self.app_name = settings.APP_NAME
        self.fronted_host = settings.FRONTEND_URL

    async def send_email(self, user, subject, context, template_name, background_tasks: BackgroundTasks):
        await send_email(
            recipients=[user.email],
            subject=subject,
            template_name=template_name,
            context=context,
            background_tasks=background_tasks
        )
