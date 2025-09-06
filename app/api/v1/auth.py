from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import *
from app.schemas.user import UserSignupRequest, UserResponse
from app.services.auth import verify_password, get_password_hash, create_access_token
from app.services.otp_service import OTPService
from datetime import timedelta

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def signup(request: UserSignupRequest, db: AsyncSession = Depends(get_db)):
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
    otp_code = await OTPService.create_otp(db, request.email, "email_verification")
    await OTPService.send_otp_email(request.email, otp_code, "email_verification")
    
    return user

@router.post("/verify-email")
async def verify_email(request: EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    # Verify OTP
    is_valid = await OTPService.verify_otp(db, request.email, request.otp_code, "email_verification")
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Update user email verification status
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if user:
        user.is_email_verified = True
        await db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")
    
    if not user.is_email_verified:
        raise HTTPException(status_code=400, detail="Please verify your email first")
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=timedelta(minutes=30)
    )
    
    return LoginResponse(
        access_token=access_token,
        user_id=user.user_id,
        is_premium=user.is_premium
    )

@router.post("/forgot-password", response_model=SendOTPResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Send password reset OTP
    otp_code = await OTPService.create_otp(db, request.email, "password_reset")
    await OTPService.send_otp_email(request.email, otp_code, "password_reset")
    
    return SendOTPResponse(message="Password reset OTP sent to your email")

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Verify OTP
    is_valid = await OTPService.verify_otp(db, request.email, request.otp_code, "password_reset")
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Update user password
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(request.new_password)
    await db.commit()
    
    return {"message": "Password reset successfully"}