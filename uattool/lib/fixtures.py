"""Reusable setup helpers so downstream scripts don't depend on an earlier
script's leftover data (each catalog row must also work when run alone via
`run_uat.py --only <row>`).
"""

import os
import time
from urllib.parse import quote

from . import config

FIXTURE_IMAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "test_cover_photo.jpg")


# Recognizable, real-world scenarios supplied for this suite. A timestamp is
# appended to activity/product names so every catalog row remains independently
# repeatable on the shared production UAT tenant.
LHGI_ACTIVITY_NAME = "LHGI"
LHGI_PASSPORT_TYPE = "Remplacant"
LHGI_PRICE = "50.00"
LHGI_SESSIONS = "4"

YOGA_ACTIVITY_NAME = "Yoga"
YOGA_PASSPORT_TYPE = "Regulier"
YOGA_PRICE = "200.00"
YOGA_SESSIONS = "25"
YOGA_MAT_NAME = "Tapis de yoga"
YOGA_MAT_PRICE = 50.00
YOGA_LEGGINGS_NAME = "Legging"
YOGA_LEGGINGS_PRICE = 70.00
YOGA_LEGGINGS_SIZES = "S, M, L, XL"

WING_FOIL_ACTIVITY_NAME = "Wing Foil Course"
WING_FOIL_PASSPORT_TYPE = "Cours de 2h"
WING_FOIL_PRICE = "200.00"
WING_FOIL_SESSIONS = "1"
WING_FOIL_COACHES = ("Ken", "Jerome")


def scenario_name(base_name, qualifier=None):
    """Return a recognizable fixture name that won't collide with an older run."""
    parts = [base_name]
    if qualifier:
        parts.append(qualifier)
    parts.append(f"UAT {time.time_ns()}")
    return " — ".join(parts)


def ensure_shop_enabled(page, ctx):
    """Turn SHOP_ENABLED on if it isn't. Left on afterwards — shop rows depend on it."""
    page.goto(f"{ctx.base_url}/admin/unified-settings?section=shop")
    if page.is_checked("#shop_enabled"):
        ctx.note("SHOP_ENABLED was already on.")
        return
    page.check("#shop_enabled")
    page.locator('button:has-text("Save Shop Settings")').first.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    if not page.is_checked("#shop_enabled"):
        raise AssertionError("SHOP_ENABLED did not persist as checked after saving Shop settings.")
    ctx.note("SHOP_ENABLED was off — turned it on via Settings > Shop and left it on.")


def create_product(page, ctx, name, price, with_photo=False, sizes=None):
    """Create a shop product through the real admin UI at /admin/products."""
    page.goto(f"{ctx.base_url}/admin/products")
    page.click('button[data-bs-target="#productModal"]')
    page.wait_for_selector("#productModal.show", timeout=5000)

    page.fill("#name", name)
    page.fill("#price", str(price))
    if sizes:
        page.fill("#size_label", sizes)
    if with_photo:
        page.set_input_files("#photo", FIXTURE_IMAGE)

    page.locator('#productModal button[type="submit"]').first.click()
    page.wait_for_load_state("networkidle", timeout=15000)

    if page.locator(".alert-danger, .invalid-feedback").count():
        raise AssertionError(f"Product form appears to have validation errors creating {name!r}.")

    ctx.note(f"Created product {name!r} (${float(price):.2f}, photo={'yes' if with_photo else 'no'}).")
    return name


def expand_collapsible_sections(page, ctx=None):
    """Open every collapsed <details> section on the current form.

    The style-guide redesign moved settings like show_in_shop and accept_credit_card inside
    `mp-collapsible-section` <details> elements that start closed. A closed <details> has
    `overflow: hidden` and clips its contents to a 0x0 box, so Playwright reports the fields
    inside as not visible and check()/click() time out — even though getComputedStyle still
    says display:block. Clicking the <summary> is what a real admin does to reach them.

    Returns the number of sections opened.
    """
    summaries = page.locator("details:not([open]) > summary")
    opened = 0
    for i in range(summaries.count()):
        try:
            summaries.nth(i).click(timeout=5000)
            opened += 1
        except Exception:
            # A section that refuses to open is only a problem if a later field is missing,
            # and that assertion belongs to the caller, not here.
            pass
    if opened:
        page.wait_for_timeout(200)  # let the disclosure settle before fields are touched
        if ctx:
            ctx.note(f"Expanded {opened} collapsed form section(s) to reach advanced settings.")
    return opened


def create_minimal_activity(page, ctx, name=None, workflow_type="payment_first",
                             price="1.00", sessions="1", passport_type_name="UAT Standard",
                             description=None, extra_setup=None, cover_image=None):
    """Create a throwaway activity with one passport type via the real admin UI.

    extra_setup: optional callable(page) run after the base fields are filled
    but before Save, for scripts that need extra toggles (e.g. show_in_shop,
    uses_scheduling) — keeps this helper generic instead of growing endless kwargs.
    cover_image: optional local image path uploaded through the real cover-photo field.

    Returns (activity_id, activity_name, passport_type_name).
    """
    name = name or f"UAT Fixture Activity {time.time_ns()}"

    page.goto(f"{ctx.base_url}/create-activity")
    page.fill('input[name="name"]', name)
    if description is not None:
        page.fill('textarea[name="description"]', description)

    # The latest activity form uses visible choice-card radios. The live kdc tenant may
    # run an older hidden-checkbox build, but forcing the visible radio click is the
    # forward-compatible path for the upcoming upgraded tenant.
    page.locator(f'input[name="workflow_type"][value="{workflow_type}"]').first.check()

    page.click("#addPassportTypeBtn")
    page.wait_for_selector("#addPassportTypeModal.show", timeout=5000)
    page.fill("#newPassportTypeName", passport_type_name)
    page.fill("#newPassportTypePrice", price)
    page.fill("#newPassportTypeSessions", sessions)
    page.click("#saveNewPassportType")
    page.wait_for_timeout(300)

    # Add the cover photo after the passport type so the upload/crop process has time to
    # settle before the form is submitted, and so it doesn't intercept the passport modal.
    if cover_image:
        page.set_input_files("#cover-photo-upload", cover_image)
        # The photo normalizer opens a crop modal on file selection; confirm it so the
        # cropped image is written to the hidden field and the modal is dismissed.
        page.wait_for_selector("#cropModal.show", timeout=5000)
        page.click("#cropConfirmBtn")
        page.wait_for_selector("#cropModal", state="hidden", timeout=5000)

    if extra_setup:
        # Advanced toggles (show_in_shop, accept_credit_card, uses_scheduling) live inside a
        # collapsed <details> since the style-guide redesign, and are unreachable until it opens.
        expand_collapsible_sections(page, ctx)
        extra_setup(page)

    page.locator('#activityForm button[type="submit"]').first.click()
    page.wait_for_load_state("networkidle", timeout=15000)

    # create_activity() redirects to the dashboard on success, so the activity id is no
    # longer in the URL. Resolve it from the activities list by the exact fixture name.
    page.goto(f"{ctx.base_url}/activities")
    page.wait_for_load_state("networkidle", timeout=15000)
    row = page.locator(f'tr:has-text("{name}")')
    row.wait_for(timeout=5000)
    link = row.locator('a[href*="/activity-dashboard/"]').first
    href = link.get_attribute("href")
    activity_id = next((p for p in href.rstrip("/").split("/") if p.isdigit()), None)
    if not activity_id:
        raise AssertionError(f"create_minimal_activity: couldn't parse activity id from href {href!r}")

    ctx.note(f"Fixture activity created: {name!r} (id={activity_id}, workflow={workflow_type}).")
    return activity_id, name, passport_type_name


def _require_safe_test_email(email):
    """Refuse fixture creation for anyone except Ken's approved UAT address."""
    if email != config.TEST_EMAIL:
        raise ValueError(
            f"UAT recipient safety check refused {email!r}; all test users must use "
            f"config.TEST_EMAIL ({config.TEST_EMAIL})."
        )


def create_admin_passport(page, ctx, activity_id, name=None, email=None, sold_amt=None, uses_remaining=None):
    """Create a passport directly via the real admin /create-passport form (NOT the public
    signup flow) — the same route+template behind the "Create Passport" button on
    templates/passports.html and templates/activity_dashboard.html.

    Assumes the target activity has exactly one active PassportType (true for every
    activity created by create_minimal_activity), so create_passport()'s
    single_passport_type_id logic auto-selects it and reveals #passport-final-section
    without needing to click the Activity/Passport Type selects.

    Returns the new passport's real pass_code (str), read off the "View" link
    (-> /pass/<pass_code>) in the passport's row on the activity's dashboard, since
    create_passport() doesn't render the pass_code itself before redirecting.
    """
    name = name or config.TEST_NAME
    email = email or config.TEST_EMAIL
    _require_safe_test_email(email)

    page.goto(f"{ctx.base_url}/create-passport?activity_id={activity_id}")
    page.wait_for_selector("#passport-final-section:not(.d-none)", timeout=5000)

    page.fill("#user_name", name)
    page.fill("#user_email", email)

    if sold_amt is not None:
        page.fill("#sold_amt", str(sold_amt))
    if uses_remaining is not None:
        page.fill("#uses_remaining", str(uses_remaining))

    page.locator('.card-footer button[type="submit"]').first.click()
    page.wait_for_load_state("networkidle", timeout=15000)

    if "create-passport" in page.url and page.locator(".alert-danger, .invalid-feedback").count():
        raise AssertionError(f"Passport form appears to have validation errors: {page.url}")

    # create_passport() redirects to the activity dashboard without exposing the new
    # pass_code, so look the row back up by email (the dashboard's real ?q= search,
    # scoped to this activity's passports) and read pass_code off its "View" link.
    page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}?q={email}")
    page.wait_for_load_state("networkidle", timeout=15000)
    row = page.locator(f'tr:has-text("{email}")').first
    row.wait_for(timeout=5000)
    view_link = row.locator('a.dropdown-item:has-text("View")')
    href = view_link.get_attribute("href")
    if not href:
        raise AssertionError(f"Could not find the 'View' link for the passport just created for {email!r}.")
    pass_code = href.rstrip("/").split("/")[-1]

    ctx.note(f"Admin-created passport for {name!r} <{email}> on activity {activity_id} (pass_code={pass_code}).")
    return pass_code


def fill_public_signup_form(page, ctx, activity_id, name=None, email=None, payment_method="interac"):
    """Fill (but do not submit) the public /signup/<activity_id> form as a real
    customer. Defaults to Interac (no card entry, no real charge) — pass
    payment_method="stripe" only from a money-tier script.
    """
    name = name or config.TEST_NAME
    email = email or config.TEST_EMAIL
    _require_safe_test_email(email)

    page.goto(f"{ctx.base_url}/signup/{activity_id}")

    # The real signup_form.html is a two-step JS form: contact fields (#signup-name etc.)
    # live in #step-2, which starts hidden (d-none) until "Continuer" (#continue-button) is
    # clicked on #step-1. Without this click, the fields below are not actionable and every
    # page.fill() call would hang until Playwright's actionability timeout.
    continue_button = page.locator("#continue-button")
    if continue_button.count():
        continue_button.click()
        page.wait_for_timeout(300)

    page.fill("#signup-name", name)
    page.fill("#signup-email", email)
    if page.locator("#signup-phone").count():
        page.fill("#signup-phone", "5145550000")

    method_radio = page.locator(f'input[name="payment_method"][value="{payment_method}"]:visible')
    if method_radio.count():
        method_radio.first.check()

    return page


# ================================
# Surveys (rows 07/08)
# ================================

# The auto-seeded "Post-Activity Feedback" template (app.py
# create_default_survey_template(), ~line 12859 — pre-selected in the "Create
# Survey" modal's Template dropdown) stores its questions with a "text" key,
# "text"-typed free-response questions, and {"value":..., "text":...} dict
# options. templates/survey_form.html (the real respondent-facing form)
# reads question.question (survey_form.html:396) and only branches on types
# "rating"/"multiple_choice"/"open_ended" (survey_form.html:403-439), and
# export_survey_results() (app.py:14031) reads question['question'] too —
# none of that matches the default template's format. Real, standing bugs:
# picking that template renders blank question text, leaves the two "text"
# questions with no answer input at all, shows raw dict reprs as multiple-
# choice option labels/values, and makes the CSV export redirect back with
# an error (KeyError on 'question') instead of downloading. Out of scope to
# fix here — find_or_create_reliable_survey_template() below just avoids
# that path so the rest of the survey flow is reliable, and prefers the
# OTHER auto-seeded template, "Sondage d'Activité - Simple (questions)"
# (app.py create_french_simple_survey_template(), ~line 12952), which uses
# the compatible "question"/"open_ended"/string-option format throughout.
RELIABLE_SURVEY_TEMPLATE_NAME = "Sondage d'Activité - Simple (questions)"


def find_or_create_reliable_survey_template(page, ctx):
    """Return (template_id, template_name) for a SurveyTemplate compatible
    with survey_form.html/export_survey_results() — see
    RELIABLE_SURVEY_TEMPLATE_NAME docstring above for why this isn't just
    "whichever template is pre-selected".

    Prefers the auto-seeded French template if present; otherwise builds a
    minimal compatible template from scratch via /create-survey-template
    (e.g. a tenant reset before any admin login ever ran the one-time
    SurveyTemplate.query.count() == 0 seeding in app.py).
    """
    page.goto(f"{ctx.base_url}/surveys")
    page.click('[data-bs-toggle="modal"][data-bs-target="#quickSurveyModal"]')
    page.wait_for_selector("#quickSurveyModal.show", timeout=5000)

    option = page.locator(f'#templateSelect option[data-name="{RELIABLE_SURVEY_TEMPLATE_NAME}"]')
    found = option.count() > 0
    template_id = option.first.get_attribute("value") if found else None

    page.locator('#quickSurveyModal .modal-header button[data-bs-dismiss="modal"]').first.click()
    page.wait_for_timeout(300)

    if found:
        ctx.note(
            f"Using existing seeded survey template {RELIABLE_SURVEY_TEMPLATE_NAME!r} "
            f"(id={template_id}) — compatible with the respondent form and CSV export, "
            f"unlike the pre-selected default 'Post-Activity Feedback' (see "
            f"lib/fixtures.py RELIABLE_SURVEY_TEMPLATE_NAME for the real bugs that template hits)."
        )
        return template_id, RELIABLE_SURVEY_TEMPLATE_NAME

    ctx.note(
        f"{RELIABLE_SURVEY_TEMPLATE_NAME!r} not found among seeded templates — building a "
        f"fresh minimal compatible template via /create-survey-template."
    )
    return _build_minimal_survey_template(page, ctx)


def _build_minimal_survey_template(page, ctx):
    """Fallback: build a 2-question template (1 required multiple-choice,
    1 optional open-ended) via the real question-builder UI. That builder
    only ever emits the "question"/"open_ended"/string-option format, so
    the result is always compatible (see module notes above)."""
    name = f"UAT Minimal Template {time.time_ns()}"

    page.goto(f"{ctx.base_url}/create-survey-template")
    page.fill("#name", name)

    page.click('button:has-text("Add Question")')
    page.fill("#question_1_text", "How satisfied were you with this activity?")
    page.fill('input[name="question_1_option_1"]', "Satisfied")
    page.fill('input[name="question_1_option_2"]', "Not satisfied")

    page.click('button:has-text("Add Question")')
    page.fill("#question_2_text", "Any comments?")
    page.select_option("#question_type_2", "open_ended")

    page.locator('#templateForm button[type="submit"]').first.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    creation_flash = page.locator(".flash-alert .alert-message").all_inner_texts()

    page.goto(f"{ctx.base_url}/survey-templates?q={quote(name)}&show_all=true")
    page.wait_for_load_state("networkidle", timeout=15000)
    row = page.locator(f'tr:has-text("{name}")')
    if row.count() == 0:
        raise AssertionError(
            f"Fallback survey template {name!r} not found on /survey-templates after creation "
            f"attempt. Flash messages seen: {creation_flash}"
        )
    row = row.first
    edit_link = row.locator('a[role="menuitem"]:has-text("Edit Template")')
    href = edit_link.get_attribute("href")
    if not href:
        raise AssertionError(f"Could not find the 'Edit Template' link for template {name!r} just created.")
    template_id = href.rstrip("/").split("/")[-1]

    ctx.note(f"Built fallback survey template {name!r} (id={template_id}).")
    return template_id, name


def create_survey(page, ctx, activity_id, activity_name, template_id, survey_name=None):
    """Create a Survey for activity_id via the real "Create Survey" modal on
    templates/surveys.html (POSTs to /create-quick-survey). Returns
    (survey_id, survey_name, survey_token).
    """
    survey_name = survey_name or f"UAT Survey {time.time_ns()}"

    page.goto(f"{ctx.base_url}/surveys")
    page.click('[data-bs-toggle="modal"][data-bs-target="#quickSurveyModal"]')
    page.wait_for_selector("#quickSurveyModal.show", timeout=5000)

    page.select_option("#activitySelect", str(activity_id))
    page.wait_for_selector("#quickSurveyStep2:not(.d-none)", timeout=5000)
    page.fill("#surveyNameInput", survey_name)
    page.select_option("#templateSelect", str(template_id))
    page.wait_for_selector("#createBtn:not([disabled])", timeout=5000)

    page.locator("#createBtn").click()
    page.wait_for_load_state("networkidle", timeout=15000)
    creation_flash = page.locator(".flash-alert .alert-message").all_inner_texts()

    page.goto(f"{ctx.base_url}/surveys?q={quote(survey_name)}&show_all=true")
    page.wait_for_load_state("networkidle", timeout=15000)
    row = page.locator(f'tr:has-text("{survey_name}")')
    if row.count() == 0:
        raise AssertionError(
            f"Survey {survey_name!r} not found on /surveys after creation attempt. "
            f"Flash messages seen: {creation_flash}"
        )
    row = row.first

    menu = row.locator(".mp-action-menu")
    menu_id = menu.get_attribute("id") or ""
    survey_id = menu_id.rsplit("-", 1)[-1]
    if not survey_id.isdigit():
        raise AssertionError(f"Could not parse survey id from action menu id {menu_id!r}.")

    view_link = row.locator('a[role="menuitem"]:has-text("View Survey")')
    href = view_link.get_attribute("href")
    if not href:
        raise AssertionError(f"Could not find the 'View Survey' link for survey {survey_name!r}.")
    survey_token = href.rstrip("/").split("/")[-1]

    ctx.note(
        f"Created survey {survey_name!r} (id={survey_id}) on activity {activity_name!r} "
        f"using template id {template_id}."
    )
    return survey_id, survey_name, survey_token


def send_survey_invitations(page, ctx, survey_id, survey_name):
    """Send invitations for survey_id via the real /send-survey-invitations/<id>
    route (the row action opens a confirm modal — see confirmSendInvitations()
    in templates/surveys.html — rather than posting directly).

    Requires at least one Passport on the survey's activity: participants are
    sourced from Passport rows, not Signup rows (app.py send_survey_invitations()
    ~line 13634) — create one with create_admin_passport() first.
    """
    page.goto(f"{ctx.base_url}/surveys?q={quote(survey_name)}&show_all=true")
    page.wait_for_load_state("networkidle", timeout=15000)
    row = page.locator(f'tr:has-text("{survey_name}")').first
    row.wait_for(timeout=5000)

    row.locator('button[aria-label="Actions"]').first.click()
    page.wait_for_timeout(300)
    row.locator('[role="menuitem"]:has-text("Send Invitations")').first.click()
    page.wait_for_selector("#sendInvitationsModal.show", timeout=5000)
    page.locator('#sendInvitationsForm button[type="submit"]').click()
    page.wait_for_load_state("networkidle", timeout=15000)

    flash_text = " ".join(page.locator(".flash-alert .alert-message").all_inner_texts())
    if "error" in flash_text.lower() or not flash_text.strip():
        raise AssertionError(f"Send Invitations for {survey_name!r} did not report success: {flash_text!r}")

    ctx.note(
        f"Sent survey invitations for {survey_name!r}: {flash_text!r} — real SMTP email, this "
        f"tool has no mailbox reader; check {config.TEST_EMAIL} by hand to confirm it arrived."
    )


def submit_survey_response(page, ctx, survey_token, label="respondent"):
    """Fill and submit the public /survey/<token> respondent form generically
    — handles rating/multiple_choice/open_ended questions in the step-wizard
    UI (templates/survey_form.html), whichever compatible template is behind
    survey_token. Submits as an anonymous respondent: this tool can't read
    the real per-invitee response_token from Ken's actual inbox, so it uses
    the survey's own base token (the one on the "View Survey" action / an
    unauthenticated visit to the link) rather than the emailed one.
    """
    page.goto(f"{ctx.base_url}/survey/{survey_token}")
    page.wait_for_load_state("networkidle", timeout=15000)
    ctx.screenshot(page, f"survey_form_{label}")

    total_steps = page.locator(".survey-step").count()
    if total_steps == 0:
        raise AssertionError(f"No questions rendered on the respondent survey form at /survey/{survey_token}.")
    if total_steps != 8:
        raise AssertionError(
            f"Expected the supplied application survey to render 8 questions, found {total_steps}."
        )
    ctx.note("Confirmed the Wing Foil application survey renders all 8 questions.")

    for _ in range(total_steps):
        active = page.locator(".survey-step.active")
        active.wait_for(timeout=5000)
        option_cards = active.locator(".option-card")
        textarea = active.locator("textarea")

        if option_cards.count():
            option_cards.first.click()
            page.wait_for_timeout(700)  # JS auto-advances 400ms after a radio pick
        elif textarea.count():
            textarea.fill("Submitted by the UAT tool — safe to ignore.")
            next_btn = active.locator(".btn-next")
            if next_btn.count():
                next_btn.click()
                page.wait_for_timeout(300)

    submit_btn = page.locator(".btn-submit")
    submit_btn.scroll_into_view_if_needed()
    submit_btn.click()
    page.wait_for_load_state("networkidle", timeout=15000)
    ctx.screenshot(page, f"survey_thank_you_{label}")

    if not page.locator(".thank-you-title").count():
        raise AssertionError(
            f"Survey submission ({label}) did not reach the thank-you confirmation page "
            f"(url={page.url}) — likely a client-side required-field validation block."
        )
    ctx.note(f"Submitted survey response ({label}) for token {survey_token}.")
