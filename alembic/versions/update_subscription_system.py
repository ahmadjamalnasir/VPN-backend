"""update subscription system

Revision ID: update_subscription_system
Revises: remove_is_superuser_fix_user_id
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_subscription_system'
down_revision = 'remove_is_superuser_fix_user_id'
branch_labels = None
depends_on = None

def upgrade():
    # Update subscription_plans table
    op.drop_column('subscription_plans', 'plan_id')
    op.drop_column('subscription_plans', 'plan_type')
    op.drop_column('subscription_plans', 'price')
    op.drop_column('subscription_plans', 'is_premium')
    op.drop_column('subscription_plans', 'features')
    
    op.add_column('subscription_plans', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('subscription_plans', sa.Column('price_usd', sa.Numeric(precision=10, scale=2), nullable=False))
    op.add_column('subscription_plans', sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('subscription_plans', sa.Column('status', sa.Enum('active', 'inactive', name='planstatus'), nullable=False, server_default='active'))
    
    # Update user_subscriptions table
    op.drop_column('user_subscriptions', 'payment_method')
    op.alter_column('user_subscriptions', 'status',
                    type_=sa.Enum('active', 'expired', 'canceled', name='subscriptionstatus'),
                    nullable=False)
    op.alter_column('user_subscriptions', 'auto_renew', server_default='false')
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_method', sa.Enum('card', 'paypal', 'in_app_purchase', 'crypto', name='paymentmethod'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'success', 'failed', name='paymentstatus'), nullable=False, server_default='pending'),
        sa.Column('transaction_ref', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['user_subscriptions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create vpn_usage_logs table
    op.create_table('vpn_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('server_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True),
        sa.Column('data_used_mb', sa.BigInteger(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Drop new tables
    op.drop_table('vpn_usage_logs')
    op.drop_table('payments')
    
    # Revert user_subscriptions
    op.add_column('user_subscriptions', sa.Column('payment_method', sa.String(), nullable=True))
    op.alter_column('user_subscriptions', 'auto_renew', server_default='true')
    
    # Revert subscription_plans
    op.drop_column('subscription_plans', 'status')
    op.drop_column('subscription_plans', 'features')
    op.drop_column('subscription_plans', 'price_usd')
    op.drop_column('subscription_plans', 'description')
    
    op.add_column('subscription_plans', sa.Column('plan_id', sa.Integer(), autoincrement=True, nullable=False))
    op.add_column('subscription_plans', sa.Column('plan_type', sa.String(10), nullable=False))
    op.add_column('subscription_plans', sa.Column('price', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('subscription_plans', sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('subscription_plans', sa.Column('features', sa.String(), nullable=True))