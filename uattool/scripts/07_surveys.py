"""Row 07 — Surveys.

Creates a fixture activity + a Passport for Ken on it (send_survey_invitations()
sources participants from Passport rows, not Signup rows — see app.py ~13634),
creates a Survey tied to that activity using an existing, respondent-form-
compatible SurveyTemplate (see lib/fixtures.py's
find_or_create_reliable_survey_template() docstring for why the pre-selected
default "Post-Activity Feedback" template is deliberately NOT used — it hits
real standing bugs in both the respondent form and the CSV export), sends the
invitation email, then submits a response as the respondent on both desktop
and mobile (the respondent-facing survey form is the one real users fill on
their phones). Finally views the results page and exports the results,
confirming the download is non-empty.
"""

import csv
import os

from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import (
    create_admin_passport,
    create_minimal_activity,
    create_survey,
    find_or_create_reliable_survey_template,
    send_survey_invitations,
    submit_survey_response,
    scenario_name,
    WING_FOIL_ACTIVITY_NAME,
    WING_FOIL_COACHES,
    WING_FOIL_PASSPORT_TYPE,
    WING_FOIL_PRICE,
    WING_FOIL_SESSIONS,
)

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "downloads")


def run(ctx):
    survey_name = scenario_name("Wing Foil Course Survey")

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        activity_id, activity_name, _ = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(WING_FOIL_ACTIVITY_NAME, "Survey"),
            passport_type_name=WING_FOIL_PASSPORT_TYPE,
            price=WING_FOIL_PRICE,
            sessions=WING_FOIL_SESSIONS,
            description=(
                f"Wing Foil course coached by {WING_FOIL_COACHES[0]} and "
                f"{WING_FOIL_COACHES[1]}."
            ),
        )
        create_admin_passport(page, ctx, activity_id)

        template_id, template_name = find_or_create_reliable_survey_template(page, ctx)
        survey_id, survey_name, survey_token = create_survey(
            page, ctx, activity_id, activity_name, template_id, survey_name
        )
        ctx.screenshot(page, "survey_created")

        send_survey_invitations(page, ctx, survey_id, survey_name)

        # send_email_async() dispatches on a background thread; give the
        # EmailLog write a moment to land before searching for it.
        page.wait_for_timeout(2000)
        assert_log_contains(page, survey_name, base_url=ctx.base_url)

        # --- respondent flow, desktop first ---
        submit_survey_response(page, ctx, survey_token, label="desktop")

    # --- mobile pass: the respondent form is what real users fill on their phones ---
    with new_page(viewport="mobile") as page:
        submit_survey_response(page, ctx, survey_token, label="mobile")

    # --- back to admin: view results, export ---
    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        page.goto(f"{ctx.base_url}/survey/{survey_id}/results")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "survey_results")

        completed_cell = page.locator(
            'div.text-muted.small.text-uppercase:has-text("COMPLETED") + div'
        ).first
        completed_text = completed_cell.inner_text().strip()
        try:
            completed_count = int(completed_text)
        except ValueError:
            raise AssertionError(f"Could not parse completed-response count from {completed_text!r}.")
        if completed_count < 2:
            raise AssertionError(
                f"Expected at least 2 completed survey responses (desktop + mobile submissions) "
                f"on /survey/{survey_id}/results, found {completed_count}."
            )
        ctx.note(f"Survey results page shows {completed_count} completed response(s).")

        # --- export results ---
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        export_url = f"{ctx.base_url}/survey/{survey_id}/export"
        # page.goto() on a URL that returns an attachment raises "Download is starting"
        # before the download can be captured; a scripted navigation triggers the same
        # real browser download without that error.
        with page.expect_download(timeout=20000) as download_info:
            page.evaluate("url => { window.location.href = url; }", export_url)
        download = download_info.value
        dest_path = os.path.join(DOWNLOADS_DIR, f"07_survey_{survey_id}_{download.suggested_filename}")
        download.save_as(dest_path)

        size = os.path.getsize(dest_path)
        if size == 0:
            raise AssertionError(f"Survey results export downloaded but file is empty: {dest_path}")

        with open(dest_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows or not rows[0]:
            raise AssertionError(f"Survey results export at {dest_path} has no header row.")

        ctx.note(
            f"Exported survey results to {dest_path} ({size} bytes, {len(rows) - 1} data row(s), "
            f"header: {rows[0]!r})."
        )

    ctx.note(
        f"Row 07 complete: survey {survey_name!r} (id={survey_id}) on activity {activity_name!r} "
        f"using template {template_name!r}."
    )
