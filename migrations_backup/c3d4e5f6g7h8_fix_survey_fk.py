"""Fix survey deletion foreign key constraint

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-11-05 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix foreign key constraint for survey deletion.
    Add CASCADE to survey_response.survey_id so responses are deleted with survey.
    """

    conn = op.get_bind()

    # Disable foreign keys temporarily
    conn.execute(text("PRAGMA foreign_keys=OFF"))

    # Recreate survey_response table with CASCADE for survey_id
    conn.execute(text("""
        CREATE TABLE survey_response_new (
            id INTEGER NOT NULL PRIMARY KEY,
            survey_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            passport_id INTEGER,
            response_token VARCHAR(32) NOT NULL UNIQUE,
            responses TEXT,
            completed BOOLEAN,
            completed_dt DATETIME,
            started_dt DATETIME,
            invited_dt DATETIME,
            created_dt DATETIME,
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY(survey_id) REFERENCES survey (id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL
        )
    """))

    conn.execute(text("INSERT INTO survey_response_new (id, survey_id, user_id, passport_id, response_token, responses, completed, completed_dt, started_dt, invited_dt, created_dt, ip_address, user_agent) SELECT id, survey_id, user_id, passport_id, response_token, responses, completed, completed_dt, started_dt, invited_dt, created_dt, ip_address, user_agent FROM survey_response"))
    conn.execute(text("DROP TABLE survey_response"))
    conn.execute(text("ALTER TABLE survey_response_new RENAME TO survey_response"))
    conn.execute(text("CREATE INDEX ix_survey_response_token ON survey_response (response_token)"))
    conn.execute(text("CREATE INDEX ix_survey_response_survey ON survey_response (survey_id)"))

    # Re-enable foreign keys
    conn.execute(text("PRAGMA foreign_keys=ON"))


def downgrade():
    """Revert to original FK constraint (without CASCADE)"""

    conn = op.get_bind()

    # Disable foreign keys temporarily
    conn.execute(text("PRAGMA foreign_keys=OFF"))

    # Revert survey_response table
    conn.execute(text("""
        CREATE TABLE survey_response_new (
            id INTEGER NOT NULL PRIMARY KEY,
            survey_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            passport_id INTEGER,
            response_token VARCHAR(32) NOT NULL UNIQUE,
            responses TEXT,
            completed BOOLEAN,
            completed_dt DATETIME,
            started_dt DATETIME,
            invited_dt DATETIME,
            created_dt DATETIME,
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY(survey_id) REFERENCES survey (id),
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL
        )
    """))

    conn.execute(text("INSERT INTO survey_response_new SELECT * FROM survey_response"))
    conn.execute(text("DROP TABLE survey_response"))
    conn.execute(text("ALTER TABLE survey_response_new RENAME TO survey_response"))

    # Re-enable foreign keys
    conn.execute(text("PRAGMA foreign_keys=ON"))
