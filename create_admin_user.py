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
        # Create admin_users table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                admin_id SERIAL UNIQUE,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                hashed_password VARCHAR NOT NULL,
                full_name VARCHAR NOT NULL,
                role VARCHAR DEFAULT 'admin',
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Check if admin already exists
        result = await conn.fetchrow(
            "SELECT id FROM admin_users WHERE username = $1", 'admin'
        )
        if result:
            print("Admin user already exists")
            return
        
        # Create admin user
        hashed_password = get_password_hash("admin123")
        
        admin_uuid = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO admin_users (id, username, email, hashed_password, full_name, role)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            admin_uuid, "admin", "admin@primevpn.com", hashed_password, "System Administrator", "super_admin"
        )
        
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@primevpn.com")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())