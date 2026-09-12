"""Row 12 — Late payment reminders.

Creates a payment-first activity as admin, signs up as a logged-out customer
(Interac, left unpaid on purpose — mirrors row 02's pattern: a real customer
is never admin-authed), then as admin triggers the real test hook at
GET /admin/unified-settings?test_late_payment=1, which calls
send_unpaid_reminders(current_app, force_send=True) for real (app.py ~6304).

IMPORTANT — read utils.py:send_unpaid_reminders (~line 2463) before trusting
this script's assertions: the query that selects candidate passports is

    Passport.query.filter(Passport.paid == False,
                           Passport.created_dt <= cutoff_date)

where cutoff_date = now - CALL_BACK_DAYS (default 15 days, via get_setting).
`force_send=True` only bypasses the *separate* "already reminded within
CALL_BACK_DAYS" skip further down (the `if not force_send and recent_reminder
and ...` check) — it does NOT touch the `created_dt <= cutoff_date` filter in
the initial query. A signup created by this script today has created_dt ==
now, which is never <= (now - 15 days), so the fixture passport is
STRUCTURALLY INELIGIBLE to receive a reminder no matter what force_send is —
short of either changing the tenant's CALL_BACK_DAYS setting to 0 (a real
setting this UAT script shouldn't mutate) or backdating the passport's
created_dt directly in the database (out of scope for a UI-driven script).

So this script does NOT assert that our fixture signup received a reminder
email — it can't, and asserting that would be asserting something false.
Instead it asserts the one thing that's unconditionally true whenever the
hook fires: log_admin_action(f"Manual late payment reminder test by
{admin}") runs before send_unpaid_reminders() is even called, so it always
lands in the Activity Log regardless of which (if any) passports qualify.
The reminder-eligibility gap above is reported as a known limitation rather
than asserted around.

Desktop only.
"""

from lib import config
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


def run(ctx):
    # --- create the fixture activity as admin ---
    with new_page(viewport="desktop") as admin_page:
        login(admin_page, base_url=ctx.base_url)
        activity_id, activity_name, _passport_type = create_minimal_activity(
            admin_page,
            ctx,
            name=scenario_name(LHGI_ACTIVITY_NAME, "Late Payment"),
            workflow_type="payment_first",
            passport_type_name=LHGI_PASSPORT_TYPE,
            price=LHGI_PRICE,
            sessions=LHGI_SESSIONS,
        )
        ctx.note(f"Created payment-first fixture activity {activity_name!r} (id={activity_id}).")

    # --- sign up as a logged-out customer, Interac, and leave it unpaid ---
    with new_page(viewport="desktop") as guest_page:
        fill_public_signup_form(guest_page, ctx, activity_id, payment_method="interac")
        ctx.screenshot(guest_page, "unpaid_signup_form_filled")

        guest_page.locator("#submit-button").click()
        guest_page.wait_for_url("**/signup/thank-you/*", timeout=15000)
        ctx.screenshot(guest_page, "unpaid_signup_thank_you")

        url = guest_page.url
        signup_id = next((p for p in url.rstrip("/").split("/") if p.isdigit()), None)
        if not signup_id:
            raise AssertionError(f"Could not parse signup_id from thank-you URL {url!r}")

        ctx.note(
            f"Submitted unpaid Interac signup for {config.TEST_NAME} <{config.TEST_EMAIL}> "
            f"on {activity_name!r} (signup_id={signup_id}); left unpaid on purpose."
        )

    # --- back as admin: confirm the signup logged, then trigger the reminder hook ---
    with new_page(viewport="desktop") as admin_page:
        login(admin_page, base_url=ctx.base_url)

        assert_log_contains(admin_page, "Signup Submitted", base_url=ctx.base_url)
        assert_log_contains(admin_page, activity_name, base_url=ctx.base_url)
        ctx.note(f"Confirmed Activity Log shows the 'Signup Submitted' entry for {activity_name!r}.")

        admin_page.goto(f"{ctx.base_url}/admin/unified-settings?test_late_payment=1")
        admin_page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(admin_page, "after_test_late_payment_trigger")

        flash_text = admin_page.locator("body").inner_text()
        if "late payment reminder test" not in flash_text.lower():
            ctx.note(
                "Did not see the expected 'Late payment reminder test completed' flash message "
                "after the trigger — see screenshot after_test_late_payment_trigger."
            )

        # --- the one thing that's unconditionally true: the admin-action log entry ---
        expected_log_entry = f"Manual late payment reminder test by {config.ADMIN_EMAIL}"
        assert_log_contains(admin_page, expected_log_entry, base_url=ctx.base_url)
        ctx.note(f"Confirmed Activity Log entry: {expected_log_entry!r}.")

        # --- known limitation, spelled out in the report rather than faked ---
        ctx.note(
            "KNOWN LIMITATION: send_unpaid_reminders() only considers passports with "
            "created_dt <= (now - CALL_BACK_DAYS); force_send=True bypasses the "
            "'already reminded recently' skip only, not that created_dt filter. A "
            "same-day fixture signup can therefore never actually receive a reminder "
            "from this test hook, so this script does not (and cannot honestly) assert "
            "that the 'latePayment' email was sent for its own fixture signup — it only "
            "confirms the admin trigger path runs and is logged."
        )
