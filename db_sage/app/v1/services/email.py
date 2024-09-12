from fastapi import BackgroundTasks

from db_sage.app.v1.models.user import User
from db_sage.app.core.base.email import BaseEmailSender
from db_sage.app.core.config.security import hash_password
from db_sage.app.utils.email_context import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD

class SendAccountVerificationEmail(BaseEmailSender):
    async def send(self, user: User, background_tasks: BackgroundTasks):
        string_context = user.get_context_string(USER_VERIFY_ACCOUNT)
        token = hash_password(string_context) # hashed token
        activate_url = f"{self.fronted_host}/auth/account-verify?token={token}&email={user.email}"
        data = {
            'app_name': self.app_name,
            'name': user.last_name,
            'activate_url': activate_url
        }
        subject = f"Account Verification - {self.app_name}"
        await self.send_email(user, subject, data, "user/account-verification.html", background_tasks)

class SendAccountActivationConfirmationEmail(BaseEmailSender):
    async def send(self, user: User, background_tasks: BackgroundTasks):
        data = {
            'app_name': self.app_name,
            'name': user.last_name,
            'login_url': self.fronted_host
        }
        subject = f"Welcome - {self.app_name}"
        await self.send_email(user, subject, data, "user/account-verification-confirmation.html", background_tasks)

class SendPasswordResetEmail(BaseEmailSender):
    async def send(self, user: User, background_tasks: BackgroundTasks):
        string_context = f"{user.get_context_string(FORGOT_PASSWORD)}"
        token = hash_password(string_context) # hashed token
        reset_url = f"{self.fronted_host}/reset-password?token={token}&email={user.email}"
        data = {
            'app_name': self.app_name,
            'name': user.last_name,
            'activate_url': reset_url
        }
        subject = f"Reset Password - {self.app_name}"
        await self.send_email(user, subject, data, "user/password-reset.html", background_tasks)

account_verification_email = SendAccountVerificationEmail()
account_activation_confirmation_email = SendAccountActivationConfirmationEmail()
password_reset_email = SendPasswordResetEmail()