from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from fastapi.background import BackgroundTasks

from db_sage.app.utils.settings import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    MAIL_DEBUG=True,
    VALIDATE_CERTS=True,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates",
    USE_CREDENTIALS=True
)

fm = FastMail(conf)

async def send_email(recipients: list, subject: str, context: dict, template_name: str, background_tasks: BackgroundTasks):
    """Sends mail to a list of users

    Args:
        - recipients (list): the email list to receive the email
        - subject (str): the subject of the mail
        - context (dict): the body of the mail
        - template_name (str): the template name to be used
        - background_tasks (BackgroundTasks): sends the mail in the background 
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=context,
        subtype=MessageType.html
    )

    background_tasks.add_task(fm.send_message, message, template_name=template_name)