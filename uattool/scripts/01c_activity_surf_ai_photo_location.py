"""Row 01c — Activity with AI stock photo AND location autocomplete.

Creates a "Surf Course" activity that, unlike row 01, actually DEPENDS on
two external-provider features working end-to-end instead of exercising them
best-effort and falling back to a deterministic path:

1. The AI/stock photo picker (#cover-photo-search -> Unsplash search modal)
   is searched for "surf" and a real result is selected — the test fails if
   the search errors out or no result can be picked, instead of silently
   switching to direct upload like row 01 does.
2. The Google Places location field is used to look up "Rimouski" via the
   manual Lookup button (#lookupLocationBtn -> /api/places/autocomplete ->
   /api/places/details), and the test fails if the lookup errors or no
   suggestion can be selected.

This exists because neither path had any automated coverage before: row 01
deliberately avoids depending on Unsplash, and no script touched the
location field at all. Added after a production incident where Wayne's
broken import silently skipped `csrf.exempt(geocode_api)`, breaking the
location lookup with no automated test to catch it (see git history around
2026-09-13).
"""

from urllib.parse import quote

from lib.activity_log import assert_log_contains
from lib.browser import login, new_page
from lib.fixtures import open_cover_photo_picker, open_create_activity_form, scenario_name

SURF_ACTIVITY_NAME = "Cours de Surf"
SURF_PASSPORT_TYPE = "Cours d'essai"
SURF_PRICE = "75.00"
SURF_SESSIONS = "1"
SURF_PHOTO_SEARCH_TERM = "surf"
SURF_LOCATION_QUERY = "Rimouski"


def run(ctx):
    activity_name = scenario_name(SURF_ACTIVITY_NAME)

    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)
        open_create_activity_form(page, ctx)

        page.fill('input[name="name"]', activity_name)
        page.fill(
            'textarea[name="description"]',
            "Surf course fixture created by the UAT tool to test the AI photo "
            "picker and location lookup end-to-end. Safe to delete.",
        )

        page.click("#addPassportTypeBtn")
        page.wait_for_selector("#addPassportTypeModal.show", timeout=5000)
        page.fill("#newPassportTypeName", SURF_PASSPORT_TYPE)
        page.fill("#newPassportTypePrice", SURF_PRICE)
        page.fill("#newPassportTypeSessions", SURF_SESSIONS)
        page.click("#saveNewPassportType")
        page.wait_for_timeout(300)

        # --- AI/stock photo picker: this MUST succeed, no upload fallback ---
        open_cover_photo_picker(page)
        page.fill("#cover-photo-search", SURF_PHOTO_SEARCH_TERM)
        page.click("#cover-photo-search-button")
        page.wait_for_selector("#unsplashModal.show", timeout=10000)
        page.wait_for_selector(
            "#unsplashImages .card-img-top, #unsplashImages .alert-warning",
            timeout=15000,
        )
        ctx.screenshot(page, "photo_search_results")

        error_banner = page.locator("#unsplashImages .alert-warning")
        if error_banner.count():
            raise AssertionError(
                f"AI photo search for {SURF_PHOTO_SEARCH_TERM!r} failed instead of "
                f"returning results: {error_banner.inner_text()!r}"
            )

        results = page.locator("#unsplashImages .card-img-top")
        if results.count() == 0:
            raise AssertionError(
                f"AI photo search for {SURF_PHOTO_SEARCH_TERM!r} returned zero results."
            )

        results.first.click()
        page.wait_for_selector("#unsplashModal", state="hidden", timeout=15000)
        selected_filename = page.locator("#cover-photo-selected").input_value()
        if not selected_filename:
            raise AssertionError(
                "Selecting an AI/stock photo result did not populate "
                "#cover-photo-selected — the photo was not actually saved."
            )
        ctx.note(f"Selected AI/stock photo for {SURF_PHOTO_SEARCH_TERM!r}: {selected_filename!r}.")
        ctx.screenshot(page, "photo_selected")

        # --- Location lookup: this MUST succeed via the manual Lookup path ---
        page.fill("#locationAutocomplete", SURF_LOCATION_QUERY)
        page.click("#lookupLocationBtn")
        page.wait_for_selector(
            "#locationResults .mp-location-result, #locationError:not([hidden])",
            timeout=15000,
        )
        ctx.screenshot(page, "location_lookup_results")

        location_error = page.locator("#locationError:not([hidden])")
        if location_error.count():
            raise AssertionError(
                f"Location lookup for {SURF_LOCATION_QUERY!r} failed instead of "
                f"returning suggestions: {page.locator('#locationErrorText').inner_text()!r}"
            )

        location_results = page.locator("#locationResults .mp-location-result")
        if location_results.count() == 0:
            raise AssertionError(
                f"Location lookup for {SURF_LOCATION_QUERY!r} returned zero suggestions."
            )

        location_results.first.click()
        page.wait_for_selector("#locationConfirmed:not([hidden])", timeout=15000)

        confirmed_address = page.locator("#locationAddressFormatted").input_value()
        confirmed_coordinates = page.locator("#locationCoordinates").input_value()
        if SURF_LOCATION_QUERY.lower() not in confirmed_address.lower():
            raise AssertionError(
                f"Confirmed location {confirmed_address!r} does not mention "
                f"{SURF_LOCATION_QUERY!r}."
            )
        if not confirmed_coordinates:
            raise AssertionError("Confirmed location has no coordinates saved.")
        ctx.note(f"Confirmed location: {confirmed_address!r} ({confirmed_coordinates}).")
        ctx.screenshot(page, "location_confirmed")

        page.locator('#activityForm button[type="submit"]').first.click()
        page.wait_for_load_state("networkidle", timeout=15000)

        if "create-activity" in page.url and page.locator(".alert-danger, .invalid-feedback").count():
            raise AssertionError(f"Activity form appears to have validation errors: {page.url}")

        ctx.screenshot(page, "after_save")

        # create_activity() redirects to /dashboard on success (no id in the URL) — resolve
        # the new activity's id from /activities by its exact fixture name instead, same
        # approach as lib.fixtures.create_minimal_activity().
        page.goto(f"{ctx.base_url}/activities?q={quote(activity_name)}")
        page.wait_for_load_state("networkidle", timeout=15000)
        row = page.locator(f'tr:visible:has-text("{activity_name}")').first
        row.wait_for(timeout=5000)
        href = row.locator('a[href*="/activity-dashboard/"]').first.get_attribute("href")
        activity_id = next((part for part in href.rstrip("/").split("/") if part.isdigit()), None) if href else None
        if activity_id is None:
            raise AssertionError(f"Could not determine activity id for {activity_name!r} (href={href!r}).")

        assert_log_contains(page, "Activity Created", base_url=ctx.base_url)
        assert_log_contains(page, activity_name, base_url=ctx.base_url)

        # --- confirm the photo and location both persisted after save ---
        page.goto(f"{ctx.base_url}/edit-activity/{activity_id}")
        saved_photo = page.locator("#cover-photo-selected").input_value()
        if not saved_photo:
            saved_photo_src = page.locator("#cover-photo-preview img").get_attribute("src") or ""
            if selected_filename not in saved_photo_src:
                raise AssertionError(
                    f"AI-picked photo {selected_filename!r} did not persist after save "
                    f"(preview src={saved_photo_src!r})."
                )
        saved_address = page.locator("#locationAddressFormatted").input_value()
        saved_coordinates = page.locator("#locationCoordinates").input_value()
        if SURF_LOCATION_QUERY.lower() not in saved_address.lower():
            raise AssertionError(
                f"Saved location {saved_address!r} does not mention {SURF_LOCATION_QUERY!r} "
                f"after reload."
            )
        if saved_coordinates != confirmed_coordinates:
            raise AssertionError(
                f"Saved coordinates {saved_coordinates!r} don't match what was confirmed "
                f"before save ({confirmed_coordinates!r})."
            )
        ctx.note("Confirmed both the AI-picked photo and the Rimouski location persisted after save.")
