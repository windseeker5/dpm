"""Shared configuration for the UAT tool.

Everything in this suite runs against Ken's own demo.minipass.me tenant
(never a customer's), using the same admin credentials as local dev. See
uattool/CATALOG.md and the plan this tool was built from for why.
"""

import os

from dotenv import load_dotenv

# Loads uattool/.env if it exists (gitignored, same pattern as the app's
# own root .env) so you only have to type UAT_ADMIN_PASSWORD once, instead of
# exporting it in every terminal session. Safe to skip — plain `export
# UAT_ADMIN_PASSWORD=...` in your shell works too, this just also checks here.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Override with UAT_BASE_URL=... if ever needed, but the default target for
# this suite is deliberately the real demo.minipass.me tenant, not localhost —
# local email rendering is missing images, which defeats the point of a
# release-wide visual/email check.
BASE_URL = os.environ.get("UAT_BASE_URL", "https://demo.minipass.me").rstrip("/")

ADMIN_EMAIL = "kdresdell@gmail.com"

# Never hardcode the real password here: this repo is public, and a hardcoded
# credential in an old test script leaked once before (see .gitignore). Set
# UAT_ADMIN_PASSWORD in uattool/.env or your shell. The credential is never
# copied into tracked code, reports, or the generated catalog.
ADMIN_PASSWORD = os.environ.get("UAT_ADMIN_PASSWORD", "")

# Every User/Passport/Signup/Survey-respondent created by this suite uses this
# same real address — never a fake domain, the app sends real SMTP mail.
TEST_EMAIL = "kdresdell@gmail.com"
TEST_NAME = "Ken Dresdell"

# Optional read-only UAT inbox access for rows 13a-13h. When no password is
# configured, those rows still send both real workflow emails but report an
# explicit manual inbox check instead of claiming receipt. Keep credentials in
# uattool/.env only; they are never written to reports or tracked files.
IMAP_HOST = os.environ.get("UAT_IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.environ.get("UAT_IMAP_PORT", "993"))
IMAP_USERNAME = os.environ.get("UAT_IMAP_USERNAME", TEST_EMAIL)
IMAP_PASSWORD = os.environ.get("UAT_IMAP_PASSWORD", "")
IMAP_FOLDER = os.environ.get("UAT_IMAP_FOLDER", "INBOX")
IMAP_WAIT_SECONDS = int(os.environ.get("UAT_IMAP_WAIT_SECONDS", "90"))

# Headless by default: a full run is faster, and the live dashboard
# (lib/dashboard.py) is what you actually watch. `run_uat.py --headed` flips
# this back to a real visible Chrome window when you want to see the clicks.
# Rows 90/91 launch their own headed browser regardless — a human has to type a
# real card number into those.
HEADLESS = os.environ.get("UAT_HEADLESS", "1").lower() not in ("0", "false", "no")

# Local-only live dashboard. Never bound to anything but localhost.
DASHBOARD_PORT = int(os.environ.get("UAT_DASHBOARD_PORT", "8899"))

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    # Below Tabler's 768px breakpoint on purpose.
    "mobile": {"width": 390, "height": 844},
}

# Real-money scripts (90_*, 91_*) refuse to run unless this flag was passed
# to run_uat.py on the command line. See lib/runner.py.
CONFIRM_MONEY_FLAG = "--confirm-money"

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

# Legacy layout (runs before the dashboard existed) put screenshots here, away
# from their report. Kept only so old reports' relative paths still resolve;
# new runs write everything under reports/<run_id>/ via run_dir() below.
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")


def run_dir(run_id):
    """Self-contained folder for one run: events.jsonl, report.md, per-row dirs."""
    return os.path.join(REPORTS_DIR, run_id)
