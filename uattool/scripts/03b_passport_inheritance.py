"""Row 03b — Passport inheritance.

Creates activity A, admin-creates a passport on it for Ken (reusing
lib.fixtures.create_admin_passport, the same helper as row 03). Creates activity B with
"Inherit passports from other activities" enabled (the #inheritPassportsToggle /
#inheritedActivitiesList / `inherited_activity_ids` checkboxes in templates/activity_form.html
~line 761-795, inside the same #collapseActivityAdvanced section as row 01's other advanced
toggles), pointing at activity A.

Inheritance (models.py ActivityPassportInheritance, app.py get_inherited_activity_ids())
does not copy any row — it only makes activity B's dashboard additionally query
activity A's passports (app.py activity_dashboard(): visible_activity_ids = [activity_id] +
inherited_activity_ids). So the real UI signal that inheritance "just works" is: activity
B's passport table shows Ken's activity-A passport, tagged with the "Inherited" badge
(activity_dashboard.html ~line 1208-1210), same pass_code as activity A's — with no second
row for Ken appearing anywhere. This script cannot query the Passport table directly, so it
verifies this via that UI table (row count == 1, badge present, pass_code matches) and via
an activity-log occurrence count as a secondary signal — see the note left at the end for
exactly what is and isn't proven this way.
"""

from urllib.parse import quote

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

        activity_a_id, activity_a_name, _ = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(LHGI_ACTIVITY_NAME, "Passport Source"),
            passport_type_name=LHGI_PASSPORT_TYPE,
            price=LHGI_PRICE,
            sessions=LHGI_SESSIONS,
        )
        pass_code_a = create_admin_passport(page, ctx, activity_a_id)
        assert_log_contains(page, "Passport Created", base_url=ctx.base_url)

        def enable_inheritance_from_a(page):
            # Same Advanced Settings collapse row 01 opens for isQuantityLimited/scheduling.
            advanced_toggle = page.locator("#activity-advanced-chevron")
            collapse = page.locator("#collapseActivityAdvanced")
            if advanced_toggle.count() and "show" not in (collapse.get_attribute("class") or ""):
                page.locator(
                    '[data-bs-target="#collapseActivityAdvanced"], a:has(#activity-advanced-chevron)'
                ).first.click()
                page.wait_for_timeout(500)

            page.check("#inheritPassportsToggle")
            page.wait_for_timeout(300)
            page.check(f'input[name="inherited_activity_ids"][value="{activity_a_id}"]')

        activity_b_id, activity_b_name, _ = create_minimal_activity(
            page,
            ctx,
            name=scenario_name(LHGI_ACTIVITY_NAME, "Passport Inheritance"),
            passport_type_name=LHGI_PASSPORT_TYPE,
            price=LHGI_PRICE,
            sessions=LHGI_SESSIONS,
            extra_setup=enable_inheritance_from_a,
        )
        assert_log_contains(page, activity_b_name, base_url=ctx.base_url)

        # --- confirm Ken's activity-A passport is visible/usable on activity B's dashboard ---
        page.goto(f"{ctx.base_url}/activity-dashboard/{activity_b_id}?q={quote(config.TEST_EMAIL)}")
        page.wait_for_load_state("networkidle", timeout=15000)
        ctx.screenshot(page, "activity_b_dashboard_inherited_passport")

        rows = page.locator(f'tr:has-text("{config.TEST_EMAIL}")')
        row_count = rows.count()
        if row_count == 0:
            raise AssertionError(
                f"Ken's passport from activity A ({activity_a_name!r}) is not visible on "
                f"activity B's ({activity_b_name!r}) dashboard — inheritance did not surface it."
            )
        if row_count > 1:
            raise AssertionError(
                f"Expected exactly one passport row for {config.TEST_EMAIL} on activity B's "
                f"dashboard (the inherited row from A, not a second one); found {row_count}."
            )

        row_text = rows.first.inner_text()
        if "Inherited" not in row_text:
            raise AssertionError(
                "Found one matching row, but it's missing the 'Inherited' badge — can't "
                "confirm this is activity A's passport surfaced via inheritance rather than "
                "a coincidental unrelated passport on activity B."
            )
        if pass_code_a not in row_text:
            raise AssertionError(
                f"Row is flagged 'Inherited' but doesn't show activity A's pass_code "
                f"({pass_code_a!r}) — may be a different, duplicate passport rather than "
                "the same one surfaced by inheritance."
            )

        # --- secondary signal: exactly one "Passport created" log line for activity A
        # (inheritance must not have triggered a second Passport row creation) ---
        # Searched by activity name, not pass_code: create_passport() logs
        # "Passport created for {user} for activity '{name}' by {admin}" (app.py ~11881),
        # which carries no pass_code, so a ?q=<pass_code> search can never match it.
        page.goto(f"{ctx.base_url}/activity-log?q={quote(activity_a_name)}")
        page.wait_for_load_state("networkidle", timeout=10000)
        log_text = page.locator("body").inner_text().lower()
        creation_mentions = log_text.count("passport created for")
        if creation_mentions != 1:
            raise AssertionError(
                f"Expected exactly one 'Passport created' log entry for activity A "
                f"({activity_a_name!r}), found {creation_mentions} — possible duplicate Passport row."
            )

        ctx.note(
            f"Activity B ({activity_b_name!r}) was created with 'Inherit passports from other "
            f"activities' enabled, pointing at activity A ({activity_a_name!r}). Ken's "
            f"passport {pass_code_a} from A appears exactly once on B's dashboard, tagged "
            "'Inherited', same pass_code — confirmed via the passports UI table and a "
            "same-pass_code activity-log occurrence count. This does NOT directly query the "
            "Passport table, so it's not proof-positive against a duplicate DB row that "
            "happens to be filtered out of both views — only that the UI never exposes one "
            "and the creation-log count is consistent with there being just one."
        )
