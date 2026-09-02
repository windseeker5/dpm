"""normalize_activity_status_inactive_to_archived

Revision ID: d1a7e42b9c03
Revises: c8f3a2d91b45
Create Date: 2026-09-02

Activity.status used two different spellings for the same "archived" state:
the Edit Activity toggle writes 'archived', while an older set of archive
routes wrote 'inactive'. Several status checks across the app only matched
one spelling or the other, so activities archived through different entry
points behaved inconsistently (e.g. the bulk-close-passports callout only
showed for 'inactive' activities). This migration backfills existing
'inactive' rows to 'archived' so the whole app can standardize on one value.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1a7e42b9c03'
down_revision = 'c8f3a2d91b45'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE activity SET status = 'archived' WHERE status = 'inactive'")


def downgrade():
    # Data-only fix; rows originally 'inactive' vs 'archived' can no longer be
    # distinguished, so there's nothing meaningful to revert.
    pass
