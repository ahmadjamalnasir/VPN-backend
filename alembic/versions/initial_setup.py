"""initial database setup

Revision ID: initial_setup
Revises: 
Create Date: 2025-08-31 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'initial_setup'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_type', sa.String(10), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=True)
    op.create_check_constraint(
        'valid_plan_type',
        'subscriptions',
        sa.text("plan_type IN ('monthly', 'yearly', 'free')")
    )
    op.create_check_constraint(
        'valid_status',
        'subscriptions',
        sa.text("status IN ('active', 'past_due', 'canceled')")
    )

    # Create vpn_servers table
    op.create_table(
        'vpn_servers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('hostname', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('public_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('current_load', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ping', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('available_ips', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index(op.f('ix_vpn_servers_location'), 'vpn_servers', ['location'])
    op.create_check_constraint(
        'valid_server_status',
        'vpn_servers',
        sa.text("status IN ('active', 'maintenance', 'offline')")
    )

    # Create connections table
    op.create_table(
        'connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('server_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vpn_servers.id', ondelete='SET NULL')),
        sa.Column('client_ip', sa.String(), nullable=False),
        sa.Column('client_public_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='connected'),
        sa.Column('bytes_sent', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('bytes_received', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    op.create_index(op.f('ix_connections_user_id'), 'connections', ['user_id'])
    op.create_index(op.f('ix_connections_server_id'), 'connections', ['server_id'])
    op.create_check_constraint(
        'valid_connection_status',
        'connections',
        sa.text("status IN ('connected', 'disconnected')")
    )

def downgrade():
    op.drop_constraint('valid_connection_status', 'connections', type_='check')
    op.drop_index(op.f('ix_connections_server_id'), table_name='connections')
    op.drop_index(op.f('ix_connections_user_id'), table_name='connections')
    op.drop_table('connections')

    op.drop_constraint('valid_server_status', 'vpn_servers', type_='check')
    op.drop_index(op.f('ix_vpn_servers_location'), table_name='vpn_servers')
    op.drop_table('vpn_servers')

    op.drop_constraint('valid_status', 'subscriptions', type_='check')
    op.drop_constraint('valid_plan_type', 'subscriptions', type_='check')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_table('subscriptions')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
