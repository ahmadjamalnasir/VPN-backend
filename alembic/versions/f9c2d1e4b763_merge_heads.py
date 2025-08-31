"""merge heads

Revision ID: f9c2d1e4b763
Revises: 21f3b81ed058, e8f7d4b3a952
Create Date: 2025-08-31 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f9c2d1e4b763'
down_revision = ('21f3b81ed058', 'e8f7d4b3a952')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
