"""Row 05 — Announcements & Discord.

On a fresh fixture activity, defines/saves a real Discord webhook URL through
the activity form's own Settings UI (the setup step, not just firing at an
already-configured webhook) using the form's built-in "Test" button to verify
it's reachable before saving. Then sends a real announcement — email always,
Discord too when a webhook was configured — through the actual
/send-announcement/<activity_id> flow used by admins in production.

The Discord webhook URL is never hard-coded here: it's read from the
UAT_DISCORD_WEBHOOK_URL environment variable (Ken's real Discord channel
webhook). When that env var is unset, the Discord setup/test/post
assertions are skipped with a clear note, but the email announcement half
still runs and is still verified end-to-end.
"""

import os

from lib import config
from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import (
    WING_FOIL_ACTIVITY_NAME,
    WING_FOIL_COACHES,
    WING_FOIL_PASSPORT_TYPE,
    WING_FOIL_PRICE,
    WING_FOIL_SESSIONS,
    create_admin_passport,
    create_minimal_activity,
    expand_collapsible_sections,
    scenario_name,
)

ANNOUNCEMENT_MESSAGE_HTML = "<p>This is a UAT test announcement. Safe to ignore.</p>"


def _open_announcement_modal(page):
    """Open the Actions dropdown and click Send Announcement — works for
    whichever of the desktop/mobile duplicated dropdown triggers is
    currently visible at the page's viewport."""
    # The activity dashboard's "Manage" menu is dropdown_menu(id="activity-header-actions")
    # (activity_dashboard.html ~line 242), so its trigger is #activity-header-actions-trigger
    # and its entries render as [role="menuitem"] — the old Bootstrap
    # data-bs-toggle="dropdown" trigger and .dropdown-item entries no longer exist.
    page.locator("#activity-header-actions-trigger").click()
    page.wait_for_timeout(300)
    page.locator('[role="menuitem"][data-bs-target="#announcementModal"]').first.click()
    page.wait_for_selector("#announcementModal.show", timeout=5000)
    # tinymce.init() is async and registers the editor before it finishes wiring up, so
    # waiting only for tinymce.get() to return an object lets setContent() run against a
    # half-built editor whose content is then wiped when init completes. Wait for the
    # editor to report itself initialized instead.
    page.wait_for_function(
        """() => {
            if (typeof tinymce === 'undefined') return false;
            const editor = tinymce.get('announcementMessage');
            return !!editor && editor.initialized === true;
        }""",
        timeout=10000,
    )


def _fill_announcement(page, subject):
    page.fill("#announcementSubject", subject)
    # setContent() only updates TinyMCE's own iframe; the underlying <textarea> stays
    # empty until the editor is saved back to it, so the form's own validation would
    # reject this as "Please fill in both subject and message."
    page.evaluate(
        """html => {
            const editor = tinymce.get('announcementMessage');
            editor.setContent(html);
            editor.save();
        }""",
        ANNOUNCEMENT_MESSAGE_HTML,
    )


def run(ctx):
    webhook_url = os.environ.get("UAT_DISCORD_WEBHOOK_URL", "").strip()
    if webhook_url:
        ctx.note("UAT_DISCORD_WEBHOOK_URL is set — exercising the full Discord setup + post flow.")
    else:
        ctx.note(
            "UAT_DISCORD_WEBHOOK_URL is not set in the environment — skipping the Discord "
            "webhook setup/test/post assertions for this run. Set it to Ken's real Discord "
            "channel webhook URL (Discord server -> Settings -> Integrations -> Webhooks) "
            "to exercise that half of row 05. The email announcement half still runs below."
        )

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        activity_id, activity_name, _ = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(WING_FOIL_ACTIVITY_NAME, "Announcement"),
            passport_type_name=WING_FOIL_PASSPORT_TYPE,
            price=WING_FOIL_PRICE,
            sessions=WING_FOIL_SESSIONS,
            description=(
                f"Wing Foil course coached by {WING_FOIL_COACHES[0]} and "
                f"{WING_FOIL_COACHES[1]}."
            ),
        )
        create_admin_passport(page, ctx, activity_id)
        ctx.note(
            f"Created the Wing Foil subscriber as {config.TEST_NAME} <{config.TEST_EMAIL}>; "
            "the real announcement email must therefore target Ken, never another customer."
        )

        # --- setup step: define/save a real Discord webhook through the activity form ---
        if webhook_url:
            page.goto(f"{ctx.base_url}/edit-activity/{activity_id}")

            # Settings moved into <details class="mp-collapsible-section"> in the style-guide
            # redesign; the old #activity-advanced-chevron collapse matches nothing now.
            expand_collapsible_sections(page, ctx)

            page.check("#discordToggle")
            page.wait_for_timeout(300)
            page.fill("#discordWebhookUrl", webhook_url)

            # Use the form's own "Test" button to confirm the webhook is reachable
            # before saving it — this is the real wiring check, not just a POST.
            page.click("#discordTestBtn")
            page.wait_for_selector(".flash-alert .alert-message", timeout=15000)
            test_flash_text = page.locator(".flash-alert .alert-message").last.inner_text()
            ctx.screenshot(page, "discord_webhook_test_result")

            if "sent to discord" not in test_flash_text.lower():
                raise AssertionError(f"Discord webhook test did not report success: {test_flash_text!r}")
            ctx.note(f"Discord webhook test succeeded: {test_flash_text!r}")

            page.locator('#activityForm button[type="submit"]').first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            ctx.note(f"Saved Discord webhook URL on activity id {activity_id}.")

        # --- compose and send the real announcement ---
        page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}")
        _open_announcement_modal(page)

        if webhook_url:
            if not page.locator("#send_to_discord").count():
                raise AssertionError(
                    "Discord webhook was saved but the 'Also post to Discord channel' "
                    "checkbox did not appear in the announcement modal."
                )
            if not page.is_checked("#send_to_discord"):
                page.check("#send_to_discord")
            ctx.note("'Also post to Discord channel' checkbox is present and checked.")

        _fill_announcement(page, subject=f"UAT announcement for {activity_name}")
        ctx.screenshot(page, "announcement_compose_desktop")

        prior_alert_count = page.locator(".flash-alert .alert-message").count()
        page.click("#announcementSendBtn")
        page.wait_for_function(
            "count => document.querySelectorAll('.flash-alert .alert-message').length > count",
            arg=prior_alert_count,
            timeout=20000,
        )
        send_flash_text = page.locator(".flash-alert .alert-message").last.inner_text()
        ctx.screenshot(page, "announcement_sent_confirmation")

        if "announcement sent to" not in send_flash_text.lower():
            raise AssertionError(f"Announcement send did not report success: {send_flash_text!r}")
        ctx.note(f"Announcement send confirmed by UI: {send_flash_text!r}")
        ctx.note(
            f"Email announcement was sent via real SMTP to {config.TEST_EMAIL} — check the "
            "inbox by hand to confirm it arrived with images; this tool has no mailbox reader."
        )
        if webhook_url:
            ctx.note(
                "Discord announcement was posted via the real webhook — check Ken's Discord "
                "channel by hand to confirm the message appeared."
            )

        assert_log_contains(page, "Announcement sent", base_url=ctx.base_url)
        assert_log_contains(page, activity_name, base_url=ctx.base_url)

    # --- mobile pass: confirm the announcement-composing UI renders correctly on a phone ---
    # (compose only — does not submit, to avoid a duplicate send tripping the
    # 30-second idempotency guard on /send-announcement/<activity_id>)
    with new_page(viewport="mobile") as page:
        login(page, base_url=ctx.base_url)
        page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}")
        _open_announcement_modal(page)
        _fill_announcement(page, subject=f"UAT announcement for {activity_name} (mobile check)")
        ctx.screenshot(page, "announcement_compose_mobile")
        ctx.note("Confirmed announcement-composing UI renders on mobile (390px); not submitted from mobile.")
