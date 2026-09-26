"""Row 02b — Signup (approval-first, no photo).

Creates a fresh approval-first fixture activity (no cover photo, same as row
01b — create_minimal_activity() never sets one), signs up as a real customer
through the public /signup/<id> form (desktop AND mobile passes), then
approves the signup as admin via the real /signup/approve-create-pass/<id>
route (a plain GET — app.py:2523 approve_and_create_pass). The admin approval
step itself is desktop-only per the row's own instructions.
"""

from lib.activity_log import assert_log_contains
from lib.browser import login, new_page, post_as_admin, thank_you_value
from lib.fixtures import create_minimal_activity, fill_public_signup_form


def _submit_signup(page, ctx, activity_id, viewport_label):
    fill_public_signup_form(page, ctx, activity_id, payment_method="interac")
    ctx.screenshot(page, f"signup_form_filled_{viewport_label}")

    page.locator("#submit-button").click()
    page.wait_for_url("**/signup/thank-you/*", timeout=15000)
    ctx.screenshot(page, f"signup_thank_you_{viewport_label}")

    url = page.url
    signup_id = str(thank_you_value(url))
    if not signup_id:
        raise AssertionError(f"Could not parse signup_id from thank-you URL {url!r}")

    ctx.note(f"[{viewport_label}] Signup submitted (Interac), signup_id={signup_id}, landed on {url!r}.")
    return signup_id


def run(ctx):
    # --- create the no-photo, approval-first fixture activity as admin ---
    with new_page(viewport="desktop") as admin_page:
        login(admin_page, base_url=ctx.base_url)
        activity_id, activity_name, passport_type_name = create_minimal_activity(
            admin_page, ctx, workflow_type="approval_first"
        )
        ctx.note(
            f"Created approval-first, no-photo fixture activity {activity_name!r} "
            f"(id={activity_id}, passport type={passport_type_name!r})."
        )

    # --- desktop pass: sign up as a logged-out customer ---
    with new_page(viewport="desktop") as guest_page:
        ctx.note(
            "Fixture activity has no cover photo (create_minimal_activity never sets one), "
            "so the signup form's activity-photo <img> is expected to be absent — confirming "
            "the form still renders correctly with no photo, not asserting a photo."
        )
        signup_id_desktop = _submit_signup(guest_page, ctx, activity_id, "desktop")

    # --- mobile pass: the realistic case for a public signup form ---
    with new_page(viewport="mobile") as guest_page:
        signup_id_mobile = _submit_signup(guest_page, ctx, activity_id, "mobile")

    # --- admin approves the desktop signup (desktop-only step) ---
    with new_page(viewport="desktop") as admin_page:
        login(admin_page, base_url=ctx.base_url)

        assert_log_contains(admin_page, "Signup Submitted", base_url=ctx.base_url)
        ctx.note(
            f"Confirmed activity log shows 'Signup Submitted' entries for {activity_name!r} "
            f"(signup_id desktop={signup_id_desktop}, mobile={signup_id_mobile})."
        )

        post_as_admin(admin_page, f"/signup/approve-create-pass/{signup_id_desktop}", base_url=ctx.base_url)
        ctx.screenshot(admin_page, "after_approval")
        ctx.note(f"Approved signup_id={signup_id_desktop} via /signup/approve-create-pass.")

        # get_all_activity_logs() (utils.py:3853-3854) derives the "Signup Approved" log
        # type from any AdminActionLog action containing both "approved" and "signup" —
        # the literal text written at app.py:2608-2609 is
        # "Signup approved for {user} for Activity '{activity}' by {admin}".
        assert_log_contains(admin_page, "Signup Approved", base_url=ctx.base_url)
        assert_log_contains(admin_page, activity_name, base_url=ctx.base_url)
        ctx.note("Confirmed activity log shows 'Signup Approved' for the approved signup.")
