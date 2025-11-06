"""Fix passport deletion foreign key constraints (manual)

Revision ID: a1b2c3d4e5f6
Revises: backfill_created_by_financial
Create Date: 2025-11-05 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'backfill_created_by_financial'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix foreign key constraints for passport deletion.
    For SQLite, we need to recreate tables to change FK constraints.
    """

    conn = op.get_bind()

    # Disable foreign keys temporarily
    conn.execute(text("PRAGMA foreign_keys=OFF"))

    # Fix 1: signup table
    conn.execute(text("""
        CREATE TABLE signup_new (
            id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            subject VARCHAR(200),
            description TEXT,
            form_url VARCHAR(500),
            form_data TEXT,
            signed_up_at DATETIME,
            paid BOOLEAN,
            paid_at DATETIME,
            passport_id INTEGER,
            status VARCHAR(50),
            passport_type_id INTEGER,
            PRIMARY KEY (id),
            FOREIGN KEY(activity_id) REFERENCES activity (id),
            FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL,
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id)
        )
    """))

    conn.execute(text("INSERT INTO signup_new SELECT * FROM signup"))
    conn.execute(text("DROP TABLE signup"))
    conn.execute(text("ALTER TABLE signup_new RENAME TO signup"))
    conn.execute(text("CREATE INDEX ix_signup_status ON signup (status)"))

    # Fix 2: ebank_payment table
    conn.execute(text("""
        CREATE TABLE ebank_payment_new (
            id INTEGER NOT NULL PRIMARY KEY,
            timestamp DATETIME,
            from_email VARCHAR(150),
            subject TEXT,
            bank_info_name VARCHAR(100),
            bank_info_amt FLOAT,
            matched_pass_id INTEGER,
            matched_name VARCHAR(100),
            matched_amt FLOAT,
            name_score INTEGER,
            result VARCHAR(50),
            mark_as_paid BOOLEAN,
            note TEXT,
            email_received_date DATETIME,
            FOREIGN KEY(matched_pass_id) REFERENCES passport (id) ON DELETE SET NULL
        )
    """))

    conn.execute(text("INSERT INTO ebank_payment_new SELECT * FROM ebank_payment"))
    conn.execute(text("DROP TABLE ebank_payment"))
    conn.execute(text("ALTER TABLE ebank_payment_new RENAME TO ebank_payment"))

    # Fix 3: survey_response table
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
    conn.execute(text("CREATE INDEX ix_survey_response_token ON survey_response (response_token)"))
    conn.execute(text("CREATE INDEX ix_survey_response_survey ON survey_response (survey_id)"))

    # Re-enable foreign keys
    conn.execute(text("PRAGMA foreign_keys=ON"))


def downgrade():
    """Revert to original FK constraints (without ON DELETE)"""

    conn = op.get_bind()

    # Disable foreign keys temporarily
    conn.execute(text("PRAGMA foreign_keys=OFF"))

    # Revert 1: signup table
    conn.execute(text("""
        CREATE TABLE signup_new (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            passport_type_id INTEGER,
            subject VARCHAR(200),
            description TEXT,
            form_url VARCHAR(500),
            form_data TEXT,
            signed_up_at DATETIME,
            paid BOOLEAN,
            paid_at DATETIME,
            passport_id INTEGER,
            status VARCHAR(50),
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(activity_id) REFERENCES activity (id),
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id),
            FOREIGN KEY(passport_id) REFERENCES passport (id)
        )
    """))

    conn.execute(text("INSERT INTO signup_new SELECT * FROM signup"))
    conn.execute(text("DROP TABLE signup"))
    conn.execute(text("ALTER TABLE signup_new RENAME TO signup"))

    # Revert 2: ebank_payment table
    conn.execute(text("""
        CREATE TABLE ebank_payment_new (
            id INTEGER NOT NULL PRIMARY KEY,
            timestamp DATETIME,
            from_email VARCHAR(150),
            subject TEXT,
            bank_info_name VARCHAR(100),
            bank_info_amt FLOAT,
            matched_pass_id INTEGER,
            matched_name VARCHAR(100),
            matched_amt FLOAT,
            name_score INTEGER,
            result VARCHAR(50),
            mark_as_paid BOOLEAN,
            note TEXT,
            email_received_date DATETIME,
            FOREIGN KEY(matched_pass_id) REFERENCES passport (id)
        )
    """))

    conn.execute(text("INSERT INTO ebank_payment_new SELECT * FROM ebank_payment"))
    conn.execute(text("DROP TABLE ebank_payment"))
    conn.execute(text("ALTER TABLE ebank_payment_new RENAME TO ebank_payment"))

    # Revert 3: survey_response table
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
            FOREIGN KEY(passport_id) REFERENCES passport (id)
        )
    """))

    conn.execute(text("INSERT INTO survey_response_new SELECT * FROM survey_response"))
    conn.execute(text("DROP TABLE survey_response"))
    conn.execute(text("ALTER TABLE survey_response_new RENAME TO survey_response"))

    # Re-enable foreign keys
    conn.execute(text("PRAGMA foreign_keys=ON"))
