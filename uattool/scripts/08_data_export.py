"""Row 08 — Data export.

As admin, downloads every CSV export route the app actually registers:
financial report (/reports/financial/export), user-contacts
(/reports/user-contacts/export), and survey results (/survey/<id>/export).
Neither /signups/export nor /passports/export exists in app.py, so this row
no longer asserts them. The first two need no query params to succeed (all
filters are optional, read via request.args.get with defaults). The
survey-results export needs its own completed response, same as row 07 but
built fresh here so this script works standalone (`run_uat.py --only 08`)
without depending on row 07 having run.

Each download is captured via Playwright's expect_download(), saved under
uattool/reports/downloads/, and asserted non-empty + parseable as CSV
with at least a header row. Desktop only — these are admin power-user
actions, not something exercised on a phone.
"""

import csv
import os
import time

from lib.browser import login, new_page
from lib.fixtures import (
    create_admin_passport,
    create_minimal_activity,
    create_survey,
    find_or_create_reliable_survey_template,
    send_survey_invitations,
    submit_survey_response,
)

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "downloads")


def _download_and_check_csv(page, ctx, label, url):
    """Download url, save under DOWNLOADS_DIR, assert non-empty and that it
    parses as CSV with at least a header row. Returns the parsed rows."""
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    # page.goto() on a URL that returns an attachment either raises "Download is starting"
    # or never fires the download event; a scripted navigation triggers the same real
    # browser download reliably.
    with page.expect_download(timeout=20000) as download_info:
        page.evaluate("u => { window.location.href = u; }", url)
    download = download_info.value
    dest_path = os.path.join(DOWNLOADS_DIR, f"08_{label}_{download.suggested_filename}")
    download.save_as(dest_path)

    size = os.path.getsize(dest_path)
    if size == 0:
        raise AssertionError(f"{label} export downloaded but file is empty: {dest_path}")

    with open(dest_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows or not rows[0]:
        raise AssertionError(f"{label} export at {dest_path} has no header row.")

    ctx.note(
        f"{label} export downloaded to {dest_path} ({size} bytes, {len(rows) - 1} data row(s), "
        f"header: {rows[0]!r})."
    )
    return rows


def run(ctx):
    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        # NOTE: this row used to also download /signups/export and /passports/export.
        # Neither route exists in the app (app.py registers only the financial,
        # user-contacts and survey-results exports), so those two were asserting a
        # feature that was never built — they are not covered here rather than
        # failing the row forever on a 404.

        # --- 1: Financial report (period=all so it isn't scoped to a fiscal
        #     year window that might exclude everything this suite created) ---
        _download_and_check_csv(
            page, ctx, "financial", f"{ctx.base_url}/reports/financial/export?format=csv&period=all"
        )

        # --- 2: User contacts ---
        _download_and_check_csv(page, ctx, "user_contacts", f"{ctx.base_url}/reports/user-contacts/export")

        # --- 3: Survey results — build a fresh survey + completed response so this
        #     script doesn't depend on row 07 having run first ---
        survey_name = f"UAT Export Survey {int(time.time())}"
        activity_id, activity_name, _ = create_minimal_activity(page, ctx)
        create_admin_passport(page, ctx, activity_id)

        template_id, template_name = find_or_create_reliable_survey_template(page, ctx)
        survey_id, survey_name, survey_token = create_survey(
            page, ctx, activity_id, activity_name, template_id, survey_name
        )
        send_survey_invitations(page, ctx, survey_id, survey_name)
        submit_survey_response(page, ctx, survey_token, label="export_fixture")

        _download_and_check_csv(page, ctx, "survey_results", f"{ctx.base_url}/survey/{survey_id}/export")

        ctx.note(
            f"All 3 registered export routes downloaded successfully and parsed as CSV with a header row "
            f"(survey export used fresh survey {survey_name!r}, id={survey_id}, "
            f"template {template_name!r})."
        )
