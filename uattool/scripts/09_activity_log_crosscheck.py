"""Row 09 — Activity Log cross-check.

Final consolidated pass over /activity-log: confirms that the distinct log
"type" labels produced by get_all_activity_logs() (utils.py ~line 3822) each
have at least one matching entry SOMEWHERE in the log — no date/time window,
just "has this integration ever fired at all" — to catch a path that an
individual script's inline assert_log_contains() might have missed. Meant to
run after the rest of the catalog (00-08 at minimum; 10-12 too if they ran).

Uses /activity-log?type=<type> (app.py ~8054, `log_type = request.args.get
('type', ...)`, substring-matched case-insensitively against each log's
type — same pattern as the `q` search) rather than assert_log_contains()'s
`q=` search, since a `type=` filter is a more precise "does this category
exist at all" check than a text search.

The full type list, from get_all_activity_logs():
  AdminActionLog-derived: Passport Created, Passport Redeemed, Marked Paid
    (Cash/POS/TPV/Cheque/Stripe/Interac), Signup Approved, Signup Rejected,
    Signup Cancelled, Announcement Sent, Activity Created, Income
    Added/Updated/Deleted, Expense Added/Updated/Deleted, Stripe Payment
    Received, Stripe Payout Received, Admin Action (catch-all for anything
    that doesn't match a known action string, e.g. survey creation).
  EmailLog-derived: Email Sent, Email Failed, Email Dismissed.
  EbankPayment-derived: Interac Payment Matched, Payment Manually Processed,
    Payment No Match.
  ReminderLog-derived: Reminder Sent.
  Signup-derived: Signup Submitted.

Split into two groups below:
  - HARD_CHECK_TYPES: types rows 00-08 of this suite are guaranteed to
    produce (Activity Created, Passport Created/Redeemed, Announcement
    Sent, Email Sent, Signup Submitted/Approved, and the Admin Action
    catch-all that survey/product/template creation fall into) — missing
    any of these means a real integration broke somewhere in this run.
  - BEST_EFFORT_TYPES: everything else (money-tier types only rows 90/91
    or a real live Interac/Stripe payment would produce; Signup
    Rejected/Cancelled, Income/Expense CRUD, Email Failed/Dismissed,
    Reminder Sent, which no row in 00-08 exercises, and Reminder Sent
    specifically needs row 12, not part of this run) — checked and noted,
    never failed on, per the task: this row's job is to catch a MISSING
    integration, not to demand every log type fire in every run.

Desktop only.
"""

from urllib.parse import quote

from lib.browser import login, new_page

HARD_CHECK_TYPES = [
    "Activity Created",
    "Passport Created",
    "Passport Redeemed",
    "Announcement Sent",
    "Email Sent",
    "Signup Submitted",
    "Signup Approved",
    "Admin Action",
]

MONEY_TYPES = [
    "Marked Paid",
    "Stripe Payment Received",
    "Stripe Payout Received",
    "Interac Payment Matched",
    "Payment Manually Processed",
    "Payment No Match",
]

OTHER_BEST_EFFORT_TYPES = [
    "Signup Rejected",
    "Signup Cancelled",
    "Income Added",
    "Income Updated",
    "Income Deleted",
    "Expense Added",
    "Expense Updated",
    "Expense Deleted",
    "Email Failed",
    "Email Dismissed",
    "Reminder Sent",
]


def _log_type_present(page, ctx, base_url, log_type):
    url = f"{base_url}/activity-log?type={quote(log_type)}"
    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=10000)
    count = page.locator("#logTable tbody tr").count()
    return count > 0, count


def run(ctx):
    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        missing_hard = []
        for log_type in HARD_CHECK_TYPES:
            present, count = _log_type_present(page, ctx, ctx.base_url, log_type)
            if present:
                ctx.note(f"OK: {log_type!r} has {count} entr{'y' if count == 1 else 'ies'} in /activity-log.")
            else:
                missing_hard.append(log_type)
                ctx.note(f"MISSING: no /activity-log entries found for type {log_type!r}.")

        ctx.note("--- Money-tier types (require --confirm-money / rows 90-91; not checked) ---")
        for log_type in MONEY_TYPES:
            present, count = _log_type_present(page, ctx, ctx.base_url, log_type)
            if present:
                ctx.note(f"Present (bonus, not required this run): {log_type!r} has {count} entr{'y' if count == 1 else 'ies'}.")
            else:
                ctx.note(f"Not present this run (expected unless rows 90/91 ran with --confirm-money): {log_type!r}.")

        ctx.note("--- Other types not exercised by rows 00-08 (best-effort, never fails this row) ---")
        for log_type in OTHER_BEST_EFFORT_TYPES:
            present, count = _log_type_present(page, ctx, ctx.base_url, log_type)
            if present:
                ctx.note(f"Present (bonus): {log_type!r} has {count} entr{'y' if count == 1 else 'ies'}.")
            else:
                ctx.note(f"Not present this run (expected — no row in 00-08 produces {log_type!r}).")

        ctx.screenshot(page, "activity_log_overview")

        if missing_hard:
            raise AssertionError(
                f"{len(missing_hard)} activity log type(s) that rows 00-08 should have produced "
                f"are completely absent from /activity-log: {missing_hard}. This means an "
                f"integration this suite exercises earlier never actually wrote its log entry."
            )

        ctx.note(f"All {len(HARD_CHECK_TYPES)} expected activity log types are present at least once.")
