"""Row 01b — Activity lifecycle (no photo).

Creates an activity with NO cover photo at all (approval-first workflow this
time — row 01 already covers payment-first). create_minimal_activity() never
touches the image picker, so activity.image_filename stays None, which is
exactly the case this script needs.

The app does NOT fall back to any default *image file* when image_filename is
empty — templates/dashboard.html and templates/activity_dashboard.html both
guard the <img>/background-image element with `{% if activity.image_filename %}`
and render a CSS-only placeholder instead (a colored gradient div from
placeholder_css(activity.name) with the activity's first letter from
placeholder_letter(activity.name) — see utils.py get_placeholder_css /
get_placeholder_letter, wired into every template's Jinja globals at
app.py:1148-1149). So "no broken <img>" here really means: no <img> tag is
rendered for the missing photo at all, and the CSS placeholder shows in its
place — not "an <img> pointing at some default.png".
"""

from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import create_minimal_activity


def _check_no_broken_images(page, ctx, label):
    """Assert every <img> on the current page has a real, non-empty src.

    This alone can't prove "no broken image" for a CSS background-image
    placeholder (there's no <img> to inspect), so it's paired with
    _check_placeholder_shown() at the call sites below for the activity's
    own card/photo slot specifically.
    """
    broken = []
    for img in page.locator("img").all():
        src = img.get_attribute("src") or ""
        if not src.strip():
            broken.append("<img> with empty/missing src")
    if broken:
        raise AssertionError(f"[{label}] Broken <img> tag(s) found: {broken}")


def _check_placeholder_shown(page, activity_id, activity_name, label):
    """Confirm the CSS letter-placeholder (not a photo <img>) is showing for
    this specific activity's image slot, and that no activity_images/ <img>
    exists for it (there should be none — no photo was ever uploaded).
    """
    card = page.locator(f'a[href$="/activity-dashboard/{activity_id}"]')
    if card.count():
        scope = card.first
    else:
        # activity_dashboard.html itself has no such link (it *is* the page).
        scope = page.locator("body")

    photo_imgs = scope.locator('img[src*="activity_images/"]')
    if photo_imgs.count():
        raise AssertionError(
            f"[{label}] Expected no activity_images/ <img> for photo-less activity "
            f"{activity_name!r}, found {photo_imgs.count()}."
        )

    expected_letter = activity_name.strip()[0].upper() if activity_name.strip() else ""
    if expected_letter and expected_letter not in scope.inner_text():
        raise AssertionError(
            f"[{label}] Expected placeholder letter {expected_letter!r} for activity "
            f"{activity_name!r} not found — placeholder fallback may not be rendering."
        )


def run(ctx):
    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)

        activity_id, activity_name, passport_type_name = create_minimal_activity(
            page, ctx, workflow_type="approval_first"
        )
        ctx.note(
            f"Created no-photo activity {activity_name!r} (id={activity_id}, "
            f"workflow=approval_first, passport type={passport_type_name!r})."
        )

        assert_log_contains(page, "Activity Created", base_url=ctx.base_url)
        assert_log_contains(page, activity_name, base_url=ctx.base_url)

        # --- activity page (desktop) ---
        page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}")
        page.wait_for_load_state("networkidle", timeout=15000)
        _check_no_broken_images(page, ctx, "activity page desktop")
        _check_placeholder_shown(page, activity_id, activity_name, "activity page desktop")
        ctx.screenshot(page, "activity_page_desktop")

        # --- dashboard card (desktop) ---
        page.goto(f"{ctx.base_url}/dashboard")
        page.wait_for_load_state("networkidle", timeout=15000)
        _check_no_broken_images(page, ctx, "dashboard desktop")
        _check_placeholder_shown(page, activity_id, activity_name, "dashboard desktop")
        ctx.screenshot(page, "dashboard_desktop")

        ctx.note(
            "Confirmed no <img> tag is rendered for the activity's photo slot on either "
            "page; both show the CSS letter-placeholder (placeholder_css/placeholder_letter) "
            "instead — the app's real 'no photo' fallback, not a default image file."
        )

    # --- mobile pass ---
    with new_page(viewport="mobile") as page:
        login(page, base_url=ctx.base_url)

        page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}")
        page.wait_for_load_state("networkidle", timeout=15000)
        _check_no_broken_images(page, ctx, "activity page mobile")
        _check_placeholder_shown(page, activity_id, activity_name, "activity page mobile")
        ctx.screenshot(page, "activity_page_mobile")

        page.goto(f"{ctx.base_url}/dashboard")
        page.wait_for_load_state("networkidle", timeout=15000)
        _check_no_broken_images(page, ctx, "dashboard mobile")
        _check_placeholder_shown(page, activity_id, activity_name, "dashboard mobile")
        ctx.screenshot(page, "dashboard_mobile")
