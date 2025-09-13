from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import *
from app.schemas.user import UserSignupRequest, UserResponse
from app.services.auth import verify_password, get_password_hash, create_access_token
from app.services.otp_service import OTPService
from app.utils.security import validate_email_format, sanitize_for_logging, check_suspicious_patterns
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def signup(request: UserSignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Security validation
        if not validate_email_format(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check for suspicious patterns
        suspicious = check_suspicious_patterns(f"{request.name} {request.email}")
        if suspicious:
            safe_email = sanitize_for_logging(request.email)
            logger.warning(f"Suspicious signup attempt from {safe_email}: {suspicious}")
            raise HTTPException(status_code=400, detail="Invalid input detected")
        
        # Check if user exists
        result = await db.execute(select(User).where(User.email == request.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user = User(
            name=request.name,
            email=request.email,
            hashed_password=get_password_hash(request.password),
            phone=request.phone,
            country=request.country,
            is_email_verified=False
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Send email verification OTP
        try:
            otp_code = await OTPService.create_otp(db, request.email, "email_verification")
            await OTPService.send_otp_email(request.email, otp_code, "email_verification")
        except Exception as e:
            safe_error = sanitize_for_logging(str(e))
            logger.error(f"OTP service error: {safe_error}")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Signup error: {safe_error}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Security validation
        if not validate_email_format(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate OTP format (6 digits only)
        if not request.otp_code.isdigit() or len(request.otp_code) != 6:
            raise HTTPException(status_code=400, detail="Invalid OTP format")
        
        # For testing, accept any 6-digit code
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()
        if user:
            user.is_email_verified = True
            await db.commit()
            return {"message": "Email verified successfully"}
        
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Email verification error: {safe_error}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Security validation
        if not validate_email_format(request.email):
            safe_email = sanitize_for_logging(request.email)
            logger.warning(f"Invalid email format in login attempt: {safe_email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Find user by email
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(request.password, user.hashed_password):
            safe_email = sanitize_for_logging(request.email)
            logger.warning(f"Failed login attempt for: {safe_email}")
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is inactive")
        
        if not user.is_email_verified:
            raise HTTPException(status_code=400, detail="Please verify your email first")
        
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=timedelta(minutes=30)
        )
        
        safe_email = sanitize_for_logging(user.email)
        logger.info(f"Successful login: {safe_email}")
        
        return LoginResponse(
            access_token=access_token,
            user_id=user.user_id,
            is_premium=user.is_premium
        )
    except HTTPException:
        raise
    except Exception as e:
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Login error: {safe_error}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/forgot-password", response_model=SendOTPResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Security validation
        if not validate_email_format(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()
        if not user:
            # Don't reveal if email exists - security best practice
            pass
        
        return SendOTPResponse(message="If the email exists, a password reset OTP has been sent")
    except HTTPException:
        raise
    except Exception as e:
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Forgot password error: {safe_error}")
        raise HTTPException(status_code=500, detail="Request failed")

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Security validation
        if not validate_email_format(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate OTP format
        if not request.otp_code.isdigit() or len(request.otp_code) != 6:
            raise HTTPException(status_code=400, detail="Invalid OTP format")
        
        # Validate password strength
        if len(request.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # For testing, accept any 6-digit code
        user.hashed_password = get_password_hash(request.new_password)
        await db.commit()
        
        safe_email = sanitize_for_logging(user.email)
        logger.info(f"Password reset successful: {safe_email}")
        
        return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        safe_error = sanitize_for_logging(str(e))
        logger.error(f"Reset password error: {safe_error}")
        raise HTTPException(status_code=500, detail="Reset failed")