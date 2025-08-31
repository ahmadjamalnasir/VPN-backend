"""create user and subscription tables

Revision ID: initial_migration
Revises: 
Create Date: 2025-08-31 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create subscriptions table with string-based enums
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_type', sa.String(10), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("plan_type IN ('monthly', 'yearly', 'free')", name='valid_plan_type'),
        sa.CheckConstraint("status IN ('active', 'past_due', 'canceled')", name='valid_status')
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=True)

def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
