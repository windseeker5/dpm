"""Row 01 — Activity lifecycle (with photo).

Creates an activity with a cover photo, exercising BOTH modes of the photo
picker (web-search, then direct upload — the final saved image is the
uploaded one, deterministic and not dependent on an external image API
returning any particular result). Turns on the major toggles: payment-first
workflow, quantity-limited capacity, session scheduling (with one slot),
Stripe accepted, shown in shop. Uses the supplied Wing Foil Course details:
a $200 one-session "Cours de 2h", Sunday September 27 at 11am and 2pm,
and coaches Ken and Jerome. Then edits and archives the activity.
"""

from urllib.parse import quote

import os
from datetime import date

from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import (
    WING_FOIL_ACTIVITY_NAME,
    WING_FOIL_COACHES,
    WING_FOIL_PASSPORT_TYPE,
    WING_FOIL_PRICE,
    WING_FOIL_SESSIONS,
    expand_collapsible_sections,
    open_cover_photo_picker,
    open_create_activity_form,
    scenario_name,
)

FIXTURE_IMAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "test_cover_photo.jpg")


def _next_sunday_september_27():
    """Return the next Sep 27 that falls on Sunday (the supplied course date)."""
    today = date.today()
    for year in range(today.year, today.year + 20):
        candidate = date(year, 9, 27)
        if candidate >= today and candidate.weekday() == 6:
            return candidate.isoformat()
    raise AssertionError("Could not find a future Sunday, September 27 fixture date.")


def run(ctx):
    activity_name = scenario_name(WING_FOIL_ACTIVITY_NAME)
    slot_date = _next_sunday_september_27()

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)
        open_create_activity_form(page, ctx)

        page.fill('input[name="name"]', activity_name)
        page.fill(
            '#activity_description',
            f"Two-hour Wing Foil course coached by {WING_FOIL_COACHES[0]} and "
            f"{WING_FOIL_COACHES[1]}. Created by the UAT tool — safe to delete.",
        )

        page.click("#addPassportTypeBtn")
        page.wait_for_selector("#addPassportTypeModal.show", timeout=5000)
        page.fill("#newPassportTypeName", WING_FOIL_PASSPORT_TYPE)
        page.fill("#newPassportTypePrice", WING_FOIL_PRICE)
        page.fill("#newPassportTypeSessions", WING_FOIL_SESSIONS)
        page.click("#saveNewPassportType")
        page.wait_for_timeout(300)

        # --- exercise the web-search picker mode first (no external result required to pass) ---
        open_cover_photo_picker(page)
        page.fill("#cover-photo-search", "Hockey")
        page.click("#cover-photo-search-button")
        page.wait_for_selector(
            "#unsplashImages .card-img-top, #unsplashImages .alert-warning", timeout=15000
        )
        ctx.screenshot(page, "photo_picker_search_results")
        ctx.note("Exercised the web-search image picker (search term submitted, results panel captured).")

        # --- close the results modal before touching fields behind it, then switch to upload mode ---
        page.click("#unsplashModal .btn-close")
        page.wait_for_selector("#unsplashModal", state="hidden", timeout=10000)
        page.check("#cover-photo-source")
        page.set_input_files("#cover-photo-upload", FIXTURE_IMAGE)
        # File selection opens a crop modal (see photo-normalizer.js); confirm it so the
        # cropped image is written to the hidden field and the modal is dismissed, rather
        # than leaving it open to block every subsequent click on the page.
        page.wait_for_selector("#cropModal.show", timeout=5000)
        page.click("#cropConfirmBtn")
        page.wait_for_selector("#cropModal", state="hidden", timeout=5000)
        ctx.screenshot(page, "photo_picker_upload_set")

        # --- open Advanced section: workflow, capacity, scheduling, stripe/shop toggles all live there ---
        expand_collapsible_sections(page, ctx)

        page.check('input[name="workflow_type"][value="payment_first"]')

        page.check("#isQuantityLimited")
        page.fill('input[name="max_sessions"]', "20")

        stripe_toggle = page.locator('input[name="accept_credit_card"]')
        if stripe_toggle.count():
            stripe_toggle.check()
            ctx.note("Enabled Stripe (accept_credit_card).")
        else:
            ctx.note("Skipped Stripe toggle — Stripe is not configured on this tenant, so the field doesn't render.")
        page.check('input[name="show_in_shop"]')

        # --- supplied scheduling scenario: Sunday Sep 27 at 11am and 2pm ---
        page.check("#usesScheduling")
        page.wait_for_timeout(300)
        for slot_time in ("11:00", "14:00"):
            page.fill("#singleSlotDateInput", slot_date)
            page.select_option("#singleSlotTimeInput", slot_time)
            page.fill("#singleSlotCapacityInput", "10")
            add_btn = page.locator("#addSingleSlotBtn")
            if not add_btn.is_enabled():
                raise AssertionError(f"Wing Foil slot {slot_date} {slot_time} was not addable.")
            add_btn.click()
        slot_values = page.locator('input[name*="[starts_at]"]').evaluate_all(
            "els => els.map(el => el.value)"
        )
        expected_slots = [f"{slot_date}T11:00", f"{slot_date}T14:00"]
        if slot_values != expected_slots:
            raise AssertionError(f"Expected Wing Foil slots {expected_slots!r}, got {slot_values!r}.")
        ctx.note(
            f"Added Wing Foil sessions on {slot_date} at 11:00 and 14:00; "
            f"coaches {WING_FOIL_COACHES[0]} and {WING_FOIL_COACHES[1]} are named in the description."
        )

        ctx.screenshot(page, "form_filled_before_save")

        page.locator('#activityForm button[type="submit"]').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)

        if "create-activity" in page.url and page.locator(".alert-danger, .invalid-feedback").count():
            raise AssertionError(f"Activity form appears to have validation errors: {page.url}")

        ctx.screenshot(page, "after_save")
        created_url = page.url
        ctx.note(f"Created activity {activity_name!r}, landed on {created_url}")

        # create_activity() redirects to /dashboard on success (no id in the URL) — resolve
        # the new activity's id from /activities by its exact fixture name instead, same
        # approach as lib.fixtures.create_minimal_activity().
        page.goto(f"{ctx.base_url}/activities?q={quote(activity_name)}")
        page.wait_for_load_state("networkidle", timeout=15000)
        row = page.locator(f'tr:visible:has-text("{activity_name}")').first
        row.wait_for(timeout=5000)
        link = row.locator('a[href*="/activity-dashboard/"]').first
        href = link.get_attribute("href")
        activity_id = next((part for part in href.rstrip("/").split("/") if part.isdigit()), None) if href else None
        if activity_id is None:
            raise AssertionError(f"Could not determine activity id for {activity_name!r} (href={href!r}).")

        assert_log_contains(page, "Activity Created", base_url=ctx.base_url)
        assert_log_contains(page, activity_name, base_url=ctx.base_url)

        # --- confirm scenario fields persisted, then edit it ---
        page.goto(f"{ctx.base_url}/edit-activity/{activity_id}")
        saved_description = page.locator('#activity_description').input_value()
        for coach in WING_FOIL_COACHES:
            if coach not in saved_description:
                raise AssertionError(f"Expected coach {coach!r} in the saved Wing Foil description.")
        saved_slots = page.locator('input[name*="[starts_at]"]').evaluate_all(
            "els => els.map(el => el.value)"
        )
        if saved_slots != expected_slots:
            raise AssertionError(f"Expected saved Wing Foil slots {expected_slots!r}, got {saved_slots!r}.")
        if WING_FOIL_PASSPORT_TYPE not in page.locator("body").inner_text():
            raise AssertionError(f"Saved passport type {WING_FOIL_PASSPORT_TYPE!r} is not visible.")
        ctx.note("Confirmed the Wing Foil passport, coaches, and both sessions persisted after save.")

        page.fill(
            '#activity_description',
            saved_description + " Edited by the UAT tool.",
        )
        page.locator('#activityForm button[type="submit"]').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.note(f"Edited activity id {activity_id}.")

        # --- archive it ---
        page.goto(f"{ctx.base_url}/edit-activity/{activity_id}")
        status_toggle = page.locator("#statusToggle")
        if status_toggle.count():
            status_toggle.click()
            page.locator('#activityForm button[type="submit"]').first.click()
            page.wait_for_load_state("networkidle", timeout=15000)
            ctx.note(f"Archived activity id {activity_id}.")

    # --- mobile pass: confirm the create form + photo render correctly on a phone ---
    with new_page(viewport="mobile") as page:
        login(page, base_url=ctx.base_url)
        page.goto(f"{ctx.base_url}/create-activity")
        ctx.screenshot(page, "create_form_mobile")
