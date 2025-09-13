#!/usr/bin/env python3
import asyncio
import asyncpg
import uuid
from app.services.auth import get_password_hash
from app.core.config import get_settings

settings = get_settings()

async def create_admin_user():
    # Extract connection details from DATABASE_URL
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Check if admin already exists
        result = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", 'admin@gmail.com'
        )
        if result:
            print("Admin user already exists")
            return
        
        # Create admin user
        hashed_password = get_password_hash("admin")
        
        user_uuid = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO users (id, name, email, hashed_password, is_superuser, is_active, is_email_verified, is_premium)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            user_uuid, "Super Admin", "admin@gmail.com", hashed_password, True, True, True, True
        )
        
        print("Admin user created successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the database exists and migrations are run")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())