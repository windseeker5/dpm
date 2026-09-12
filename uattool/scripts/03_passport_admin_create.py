"""Row 03 — Passport (admin-direct create).

Admin creates a passport directly via /create-passport (templates/passport_form.html) —
NOT through the public /signup/<activity_id> form — for Ken's own name/email. Confirms
the resulting /pass/<pass_code> page renders a QR code and that the Activity Log records
the creation (see create_passport() in app.py ~line 12061, which logs
"Passport created for {name} for activity '{activity}' by {admin}").
"""

from lib import config
from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import (
    LHGI_ACTIVITY_NAME,
    LHGI_PASSPORT_TYPE,
    LHGI_PRICE,
    LHGI_SESSIONS,
    create_admin_passport,
    create_minimal_activity,
    scenario_name,
)


def run(ctx):
    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        activity_id, activity_name, passport_type_name = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(LHGI_ACTIVITY_NAME, "Admin Passport"),
            passport_type_name=LHGI_PASSPORT_TYPE,
            price=LHGI_PRICE,
            sessions=LHGI_SESSIONS,
        )

        pass_code = create_admin_passport(page, ctx, activity_id)

        # "Passport Created" (catalog wording) matches the real log text
        # "Passport created for ..." case-insensitively (assert_log_contains lowercases).
        assert_log_contains(page, "Passport Created", base_url=ctx.base_url)
        assert_log_contains(page, config.TEST_NAME, base_url=ctx.base_url)
        assert_log_contains(page, activity_name, base_url=ctx.base_url)

        page.goto(f"{ctx.base_url}/pass/{pass_code}")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "admin_created_passport")

        qr_img = page.locator('img[alt="Code QR du passeport"]')
        if qr_img.count() == 0:
            raise AssertionError("No QR code <img> found on /pass/<pass_code> page.")
        src = qr_img.first.get_attribute("src") or ""
        if not src.startswith("data:image/png;base64,") or len(src) < 100:
            raise AssertionError(f"QR code image src looks empty/invalid: {src[:60]!r}")

        pass_code_text = page.locator(".pass-qr-code").first.inner_text().strip()
        if pass_code_text != pass_code:
            raise AssertionError(
                f"Pass page's displayed pass_code {pass_code_text!r} doesn't match the "
                f"one read from the dashboard's View link ({pass_code!r})."
            )

        ctx.note(
            f"Passport {pass_code} created via admin /create-passport for "
            f"{config.TEST_NAME} <{config.TEST_EMAIL}> on activity {activity_name!r} "
            f"(type {passport_type_name!r}); QR code renders with a real base64 PNG."
        )
