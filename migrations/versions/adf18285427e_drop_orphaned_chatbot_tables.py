"""Drop orphaned chatbot tables

Revision ID: adf18285427e
Revises: 937a43599a19
Create Date: 2025-11-20 13:40:54.376803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adf18285427e'
down_revision = '937a43599a19'
branch_labels = None
depends_on = None


def upgrade():
    """Drop orphaned chatbot tables that are no longer used after simplification"""
    # These tables were part of the old complex chatbot system
    # They are empty (0 records) and not used by routes_simple.py
    op.execute('DROP TABLE IF EXISTS chat_usage')
    op.execute('DROP TABLE IF EXISTS chat_message')
    op.execute('DROP TABLE IF EXISTS chat_conversation')


def downgrade():
    """
    Downgrade not supported - these tables were never used in production.
    If needed, recreate from the original migration or models.py history.
    """
    pass
