"""Fix passport_type deletion foreign key constraints

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-05 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix foreign key constraints for passport_type deletion.
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
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id) ON DELETE SET NULL
        )
    """))

    conn.execute(text("INSERT INTO signup_new (id, user_id, activity_id, subject, description, form_url, form_data, signed_up_at, paid, paid_at, passport_id, status, passport_type_id) SELECT id, user_id, activity_id, subject, description, form_url, form_data, signed_up_at, paid, paid_at, passport_id, status, passport_type_id FROM signup"))
    conn.execute(text("DROP TABLE signup"))
    conn.execute(text("ALTER TABLE signup_new RENAME TO signup"))
    conn.execute(text("CREATE INDEX ix_signup_status ON signup (status)"))

    # Fix 2: passport table
    conn.execute(text("""
        CREATE TABLE passport_new (
            id INTEGER NOT NULL PRIMARY KEY,
            pass_code VARCHAR(16) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            sold_amt FLOAT,
            uses_remaining INTEGER,
            created_by INTEGER,
            created_dt DATETIME,
            paid BOOLEAN,
            paid_date DATETIME,
            marked_paid_by VARCHAR(120),
            notes TEXT,
            passport_type_id INTEGER,
            passport_type_name VARCHAR(100),
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(activity_id) REFERENCES activity (id),
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id) ON DELETE SET NULL,
            FOREIGN KEY(created_by) REFERENCES admin (id)
        )
    """))

    conn.execute(text("INSERT INTO passport_new (id, pass_code, user_id, activity_id, sold_amt, uses_remaining, created_by, created_dt, paid, paid_date, marked_paid_by, notes, passport_type_id, passport_type_name) SELECT id, pass_code, user_id, activity_id, sold_amt, uses_remaining, created_by, created_dt, paid, paid_date, marked_paid_by, notes, passport_type_id, passport_type_name FROM passport"))
    conn.execute(text("DROP TABLE passport"))
    conn.execute(text("ALTER TABLE passport_new RENAME TO passport"))
    conn.execute(text("CREATE INDEX ix_passport_pass_code ON passport (pass_code)"))

    # Fix 3: survey table
    conn.execute(text("""
        CREATE TABLE survey_new (
            id INTEGER NOT NULL PRIMARY KEY,
            activity_id INTEGER NOT NULL,
            template_id INTEGER NOT NULL,
            passport_type_id INTEGER,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            survey_token VARCHAR(32) UNIQUE NOT NULL,
            created_by INTEGER,
            created_dt DATETIME,
            status VARCHAR(50),
            email_sent BOOLEAN,
            email_sent_dt DATETIME,
            FOREIGN KEY(activity_id) REFERENCES activity (id),
            FOREIGN KEY(template_id) REFERENCES survey_template (id),
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id) ON DELETE SET NULL,
            FOREIGN KEY(created_by) REFERENCES admin (id)
        )
    """))

    conn.execute(text("INSERT INTO survey_new (id, activity_id, template_id, passport_type_id, name, description, survey_token, created_by, created_dt, status, email_sent, email_sent_dt) SELECT id, activity_id, template_id, passport_type_id, name, description, survey_token, created_by, created_dt, status, email_sent, email_sent_dt FROM survey"))
    conn.execute(text("DROP TABLE survey"))
    conn.execute(text("ALTER TABLE survey_new RENAME TO survey"))
    conn.execute(text("CREATE INDEX ix_survey_token ON survey (survey_token)"))

    # Re-enable foreign keys
    conn.execute(text("PRAGMA foreign_keys=ON"))


def downgrade():
    """Revert to original FK constraints (without ON DELETE for passport_type)"""

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
            FOREIGN KEY(passport_id) REFERENCES passport (id) ON DELETE SET NULL
        )
    """))

    conn.execute(text("INSERT INTO signup_new SELECT * FROM signup"))
    conn.execute(text("DROP TABLE signup"))
    conn.execute(text("ALTER TABLE signup_new RENAME TO signup"))

    # Revert 2: passport table
    conn.execute(text("""
        CREATE TABLE passport_new (
            id INTEGER NOT NULL PRIMARY KEY,
            pass_code VARCHAR(16) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            sold_amt FLOAT,
            uses_remaining INTEGER,
            created_by INTEGER,
            created_dt DATETIME,
            paid BOOLEAN,
            paid_date DATETIME,
            marked_paid_by VARCHAR(120),
            notes TEXT,
            passport_type_id INTEGER,
            passport_type_name VARCHAR(100),
            FOREIGN KEY(user_id) REFERENCES user (id),
            FOREIGN KEY(activity_id) REFERENCES activity (id),
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id),
            FOREIGN KEY(created_by) REFERENCES admin (id)
        )
    """))

    conn.execute(text("INSERT INTO passport_new (id, pass_code, user_id, activity_id, sold_amt, uses_remaining, created_by, created_dt, paid, paid_date, marked_paid_by, notes, passport_type_id, passport_type_name) SELECT id, pass_code, user_id, activity_id, sold_amt, uses_remaining, created_by, created_dt, paid, paid_date, marked_paid_by, notes, passport_type_id, passport_type_name FROM passport"))
    conn.execute(text("DROP TABLE passport"))
    conn.execute(text("ALTER TABLE passport_new RENAME TO passport"))

    # Revert 3: survey table
    conn.execute(text("""
        CREATE TABLE survey_new (
            id INTEGER NOT NULL PRIMARY KEY,
            activity_id INTEGER NOT NULL,
            template_id INTEGER NOT NULL,
            passport_type_id INTEGER,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            survey_token VARCHAR(32) UNIQUE NOT NULL,
            created_by INTEGER,
            created_dt DATETIME,
            status VARCHAR(50),
            email_sent BOOLEAN,
            email_sent_dt DATETIME,
            FOREIGN KEY(activity_id) REFERENCES activity (id),
            FOREIGN KEY(template_id) REFERENCES survey_template (id),
            FOREIGN KEY(passport_type_id) REFERENCES passport_type (id),
            FOREIGN KEY(created_by) REFERENCES admin (id)
        )
    """))

    conn.execute(text("INSERT INTO survey_new SELECT * FROM survey"))
    conn.execute(text("DROP TABLE survey"))
    conn.execute(text("ALTER TABLE survey_new RENAME TO survey"))

    # Re-enable foreign keys
    conn.execute(text("PRAGMA foreign_keys=ON"))
