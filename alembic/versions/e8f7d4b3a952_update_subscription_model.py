"""update subscription model

Revision ID: e8f7d4b3a952
Revises: previous_revision
Create Date: 2025-08-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e8f7d4b3a952'
down_revision = None  # Update this with your previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Create plan_type enum
    op.execute("CREATE TYPE plan_type AS ENUM ('monthly', 'yearly', 'free')")
    
    # Create subscription_status enum
    op.execute("CREATE TYPE subscription_status AS ENUM ('active', 'past_due', 'canceled')")
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_type', postgresql.ENUM('monthly', 'yearly', 'free', name='plan_type'), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'past_due', 'canceled', name='subscription_status'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=True)

def downgrade():
    # Drop the subscriptions table
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    
    # Drop the enums
    op.execute("DROP TYPE subscription_status")
    op.execute("DROP TYPE plan_type")
