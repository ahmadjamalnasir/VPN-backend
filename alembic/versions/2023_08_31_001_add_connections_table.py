"""add connections table and indexes

Revision ID: 2023_08_31_001
Revises: previous_revision
Create Date: 2023-08-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2023_08_31_001'
down_revision = 'previous_revision'  # Update this with your previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Create connections table
    op.create_table(
        'connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('server_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('client_public_key', sa.Text(), nullable=False),
        sa.Column('client_ip', postgresql.INET(), nullable=True),
        sa.Column('bytes_sent', sa.BigInteger(), default=0),
        sa.Column('bytes_received', sa.BigInteger(), default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id'])
    )

    # Create indexes
    op.create_index('ix_connections_user_id', 'connections', ['user_id'])
    op.create_index('ix_vpn_servers_location_status', 'vpn_servers', ['location', 'status'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_vpn_servers_location_status')
    op.drop_index('ix_connections_user_id')
    
    # Drop table
    op.drop_table('connections')
