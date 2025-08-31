from fastapi import APIRouter
from app.api.v1.routes import users, subscriptions, payment

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(payment.router, prefix="/payments", tags=["payments"])
