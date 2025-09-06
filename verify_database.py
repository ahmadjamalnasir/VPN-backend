#!/usr/bin/env python3
"""
Verify database table structure matches our models
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def verify_database_structure():
    print("🔍 Verifying Database Structure")
    print("=" * 40)
    
    try:
        async with engine.connect() as conn:
            # Check tables exist
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
            """
            result = await conn.execute(text(tables_query))
            tables = [row[0] for row in result.fetchall()]
            
            print("📋 Tables found:")
            for table in tables:
                print(f"   ✅ {table}")
            
            expected_tables = ['users', 'subscriptions', 'vpn_servers', 'connections', 'alembic_version']
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"   ❌ Missing tables: {missing_tables}")
            else:
                print("   ✅ All expected tables present")
            print()
            
            # Check users table structure
            print("👤 Users table structure:")
            users_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
            """
            result = await conn.execute(text(users_query))
            for row in result.fetchall():
                print(f"   {row[0]}: {row[1]} (nullable: {row[2]})")
            print()
            
            # Check foreign key relationships
            print("🔗 Foreign key relationships:")
            fk_query = """
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name;
            """
            result = await conn.execute(text(fk_query))
            for row in result.fetchall():
                print(f"   {row[0]}.{row[1]} → {row[2]}.{row[3]}")
            print()
            
            # Test basic operations
            print("🧪 Testing basic database operations:")
            
            # Test user count
            count_result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = count_result.scalar()
            print(f"   Users in database: {user_count}")
            
            # Test server count
            count_result = await conn.execute(text("SELECT COUNT(*) FROM vpn_servers"))
            server_count = count_result.scalar()
            print(f"   VPN servers in database: {server_count}")
            
            print("\n✅ Database verification completed successfully!")
            
    except Exception as e:
        print(f"❌ Database verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_database_structure())