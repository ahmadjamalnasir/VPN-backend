import random
import string
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.otp_verification import OTPVerification

class OTPService:
    @staticmethod
    def generate_otp() -> str:
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    async def create_otp(db: AsyncSession, email: str, otp_type: str) -> str:
        otp_code = OTPService.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        otp_record = OTPVerification(
            email=email,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        db.add(otp_record)
        await db.commit()
        return otp_code
    
    @staticmethod
    async def verify_otp(db: AsyncSession, email: str, otp_code: str, otp_type: str) -> bool:
        result = await db.execute(
            select(OTPVerification).where(
                OTPVerification.email == email,
                OTPVerification.otp_code == otp_code,
                OTPVerification.otp_type == otp_type,
                OTPVerification.is_used == False,
                OTPVerification.expires_at > datetime.utcnow()
            )
        )
        otp_record = result.scalar_one_or_none()
        
        if otp_record:
            otp_record.is_used = True
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def send_otp_email(email: str, otp_code: str, otp_type: str):
        # Placeholder for email sending
        print(f"📧 Sending OTP {otp_code} to {email} for {otp_type}")
        # In production, integrate with email service like SendGrid, AWS SES, etc.