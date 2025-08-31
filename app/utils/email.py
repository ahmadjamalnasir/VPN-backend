import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

async def send_verification_email(to_email: str, verification_token: str) -> None:
    """Send email verification link to user"""
    message = MIMEMultipart()
    message["From"] = settings.EMAIL_FROM_ADDRESS
    message["To"] = to_email
    message["Subject"] = "Verify your email address"

    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    html_content = f"""
    <html>
        <body>
            <h2>Welcome to Prime VPN!</h2>
            <p>Please click the button below to verify your email address:</p>
            <a href="{verification_url}" 
               style="background-color: #4CAF50; 
                      color: white; 
                      padding: 14px 25px; 
                      text-align: center; 
                      text-decoration: none; 
                      display: inline-block; 
                      border-radius: 4px;">
                Verify Email
            </a>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRES // 3600} hours.</p>
            <p>If you did not create an account with us, please ignore this email.</p>
        </body>
    </html>
    """

    message.attach(MIMEText(html_content, "html"))

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=True
        )
        await smtp.connect()
        await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.send_message(message)
        await smtp.quit()
    except Exception as e:
        # Log the error but don't raise it to avoid exposing sensitive info
        print(f"Failed to send email: {str(e)}")
