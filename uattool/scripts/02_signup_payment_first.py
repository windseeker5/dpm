"""Row 02 — Signup (payment-first).

Creates a fresh payment-first fixture activity, then signs up as a real
customer (Ken's own name/email) through the public /signup/<id> form in a
logged-out browser context — a real customer would never be admin-authed.
Runs the full create+signup flow once per viewport (desktop, then mobile),
since the signup form itself is the thing under test at each size, not just
a static screenshot of it.

fill_public_signup_form() doesn't submit the form, so this script clicks
#submit-button itself and follows the real /signup/thank-you/<signup_id>
redirect (app.py:3600, route name signup_thank_you) to recover the new
signup's id, the same way create_minimal_activity() parses the activity id
out of its own result URL.
"""

from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import (
    LHGI_ACTIVITY_NAME,
    LHGI_PASSPORT_TYPE,
    LHGI_PRICE,
    LHGI_SESSIONS,
    create_minimal_activity,
    fill_public_signup_form,
    scenario_name,
)


def _submit_signup(page, ctx, activity_id, viewport_label):
    fill_public_signup_form(page, ctx, activity_id, payment_method="interac")
    ctx.screenshot(page, f"signup_form_filled_{viewport_label}")

    page.locator("#submit-button").click()
    page.wait_for_url("**/signup/thank-you/*", timeout=15000)
    ctx.screenshot(page, f"signup_thank_you_{viewport_label}")

    url = page.url
    signup_id = next((p for p in url.rstrip("/").split("/") if p.isdigit()), None)
    if not signup_id:
        raise AssertionError(f"Could not parse signup_id from thank-you URL {url!r}")

    ctx.note(f"[{viewport_label}] Signup submitted (Interac), signup_id={signup_id}, landed on {url!r}.")
    return signup_id


def run(ctx):
    # --- create the fixture activity as admin ---
    with new_page(viewport="desktop") as admin_page:
        login(admin_page, base_url=ctx.base_url)
        activity_id, activity_name, passport_type_name = create_minimal_activity(
            admin_page,
            ctx,
            name=scenario_name(LHGI_ACTIVITY_NAME, "Signup"),
            workflow_type="payment_first",
            passport_type_name=LHGI_PASSPORT_TYPE,
            price=LHGI_PRICE,
            sessions=LHGI_SESSIONS,
        )
        ctx.note(
            f"Created payment-first fixture activity {activity_name!r} (id={activity_id}, "
            f"passport type={passport_type_name!r})."
        )

    # --- desktop pass: sign up as a logged-out customer ---
    with new_page(viewport="desktop") as guest_page:
        # This fixture activity never went through the image picker (create_minimal_activity
        # doesn't touch it), so it has no cover photo — the signup form's photo <img>
        # (templates/signup_form.html:41-45, 371-372) simply won't render here. That's a
        # property of the fixture, not a bug, so this is noted rather than asserted.
        ctx.note(
            "Fixture activity has no cover photo (create_minimal_activity never sets one), "
            "so the signup form's activity-photo <img> is expected to be absent on this pass "
            "— not asserting photo rendering, per row 02's own caveat."
        )
        signup_id_desktop = _submit_signup(guest_page, ctx, activity_id, "desktop")

    # --- mobile pass: the realistic case for a public signup form ---
    with new_page(viewport="mobile") as guest_page:
        signup_id_mobile = _submit_signup(guest_page, ctx, activity_id, "mobile")

    # --- back as admin: confirm the log and capacity ---
    with new_page(viewport="desktop") as admin_page:
        login(admin_page, base_url=ctx.base_url)

        assert_log_contains(admin_page, "Signup Submitted", base_url=ctx.base_url)
        assert_log_contains(admin_page, activity_name, base_url=ctx.base_url)
        ctx.note(
            f"Confirmed activity log shows 'Signup Submitted' entries for {activity_name!r} "
            f"(signup_id desktop={signup_id_desktop}, mobile={signup_id_mobile})."
        )

        # Capacity/seats-remaining only exists on the activity page when the activity is
        # quantity-limited (get_remaining_capacity() returns None otherwise — app.py:3431-3433).
        # create_minimal_activity() doesn't turn that toggle on, so this fixture has no visible
        # seats-remaining count to check — note instead of asserting, per the row's own caveat.
        admin_page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}")
        admin_page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(admin_page, "activity_page_after_signups")
        ctx.note(
            "Fixture activity is not quantity-limited, so it has no seats-remaining indicator "
            "to check for a decrement — this is expected, not skipped due to a failure."
        )

        # A pending signup on a payment-first activity shows the "Awaiting Payment" badge
        # (templates/activity_dashboard.html:1565/1595) — the closest UI-visible signal to
        # the catalog's "status is 'awaiting payment'" (the DB status column itself is
        # actually "pending" for Interac signups — app.py:3519 — the human-facing label is
        # derived, not the raw status string).
        if "Awaiting Payment" not in admin_page.locator("body").inner_text():
            raise AssertionError(
                f"Expected an 'Awaiting Payment' badge on the activity dashboard for "
                f"{activity_name!r} after an unpaid payment-first signup, none found."
            )
        ctx.note("Confirmed the new signup shows the 'Awaiting Payment' status badge.")
