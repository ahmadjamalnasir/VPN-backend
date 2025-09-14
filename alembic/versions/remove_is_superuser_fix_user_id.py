"""remove is_superuser and ensure user_id sequence

Revision ID: remove_is_superuser_fix_user_id
Revises: f9c2d1e4b763
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_is_superuser_fix_user_id'
down_revision = 'f9c2d1e4b763'
branch_labels = None
depends_on = None

def upgrade():
    # Create sequence for user_id if it doesn't exist
    op.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1")
    
    # Set the sequence to start from the next available number
    op.execute("""
        SELECT setval('user_id_seq', COALESCE((SELECT MAX(user_id) FROM users), 0) + 1, false)
    """)
    
    # Set default value for user_id to use the sequence
    op.execute("ALTER TABLE users ALTER COLUMN user_id SET DEFAULT nextval('user_id_seq')")
    
    # Remove is_superuser column
    op.drop_column('users', 'is_superuser')
    
    # Ensure user_id has unique constraint and index
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_user_id ON users (user_id)")

def downgrade():
    # Add back is_superuser column
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))
    
    # Remove user_id sequence default
    op.execute("ALTER TABLE users ALTER COLUMN user_id DROP DEFAULT")
    
    # Drop the sequence
    op.execute("DROP SEQUENCE IF EXISTS user_id_seq")