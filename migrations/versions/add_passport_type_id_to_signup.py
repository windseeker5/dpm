"""Add passport_type_id to signup table

Revision ID: add_passport_type_id_signup
Revises: passport_type_2025_add_passport_type_model
Create Date: 2025-06-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_passport_type_id_signup'
down_revision = 'passport_type_2025_add_passport_type_model'
branch_labels = None
depends_on = None

def upgrade():
    # Add passport_type_id column to signup table
    with op.batch_alter_table('signup', schema=None) as batch_op:
        batch_op.add_column(sa.Column('passport_type_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_signup_passport_type_id', 'passport_type', ['passport_type_id'], ['id'])

def downgrade():
    # Remove passport_type_id column from signup table
    with op.batch_alter_table('signup', schema=None) as batch_op:
        batch_op.drop_constraint('fk_signup_passport_type_id', type_='foreignkey')
        batch_op.drop_column('passport_type_id')