"""Reusable end-to-end branding/fallback scenario for catalog rows 13a-13h.

Each case controls three independent inputs: the organization logo in Settings,
the activity logo used by passport/email identity, and the activity cover photo.
The global organization setting is always restored, including after a failure.
"""

import base64
import email
import imaplib
import os
import time
from datetime import datetime, timezone
from email.header import decode_header, make_header
from urllib.parse import urljoin

from . import config
from .activity_log import assert_log_contains
from .browser import login, new_page
from .fixtures import create_minimal_activity, fill_public_signup_form, scenario_name

_FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")
COVER_IMAGE = os.path.join(_FIXTURE_DIR, "test_cover_photo.jpg")
ORG_LOGO = os.path.join(_FIXTURE_DIR, "test_org_logo.png")
ACTIVITY_LOGO = os.path.join(_FIXTURE_DIR, "test_activity_logo.png")


def _csrf(page):
    token = page.locator('input[name="csrf_token"]').first.get_attribute("value")
    if not token:
        raise AssertionError("Could not read a CSRF token from the current admin page.")
    return token


def _assert_response(response, label):
    if not response.ok:
        raise AssertionError(f"{label} failed with HTTP {response.status}: {response.text()[:300]}")


def _snapshot_org_logo(page, ctx):
    page.goto(f"{ctx.base_url}/admin/unified-settings?section=general")
    page.wait_for_load_state("networkidle", timeout=15000)
    selected_el = page.locator("input[name='selected_logo_filename'], #orgLogo-selected, #orgLogoFilename")
    selected = (selected_el.first.get_attribute("value") or "").strip()
    if not selected:
        return None
    # The settings page renders the logo through the shared image_picker macro
    # (id="orgLogo"), so the thumbnail lives in #orgLogo-preview — the old
    # #orgLogoWrapper id predates that macro and matches nothing.
    preview_img = page.locator("#orgLogo-preview img")
    if not preview_img.count():
        raise AssertionError("Settings says an organization logo exists, but its preview has no image.")
    src = preview_img.first.get_attribute("src")
    response = page.request.get(urljoin(ctx.base_url + "/", src))
    _assert_response(response, "Downloading the original organization logo for safe restoration")
    ctx.note("Saved the existing organization logo in memory so it can be restored after this case.")
    return {"name": os.path.basename(selected), "buffer": response.body()}


def _post_org_settings(page, ctx, *, logo_path=None, logo_bytes=None, logo_name=None, delete=False):
    page.goto(f"{ctx.base_url}/admin/unified-settings?section=general")
    page.wait_for_load_state("networkidle", timeout=15000)
    multipart = {
        "csrf_token": _csrf(page),
        "settings_section": "general",
        "ORG_NAME": page.locator('input[name="ORG_NAME"]').input_value(),
        "PRIMARY_BRAND_COLOR": page.locator('input[name="PRIMARY_BRAND_COLOR"]').input_value(),
        "FISCAL_YEAR_START_MONTH": page.locator('select[name="FISCAL_YEAR_START_MONTH"]').input_value(),
        "delete_logo": "1" if delete else "",
    }
    if logo_path:
        with open(logo_path, "rb") as fixture:
            logo_bytes = fixture.read()
        logo_name = os.path.basename(logo_path)
    if logo_bytes is not None:
        multipart["ORG_LOGO_FILE"] = {
            "name": logo_name or "restored_org_logo.png",
            "mimeType": "image/png",
            "buffer": logo_bytes,
        }
    response = page.request.post(
        f"{ctx.base_url}/admin/unified-settings?section=general", multipart=multipart
    )
    _assert_response(response, "Updating organization logo through Settings")


def _set_org_logo_state(page, ctx, enabled):
    if enabled:
        _post_org_settings(page, ctx, logo_path=ORG_LOGO)
    else:
        _post_org_settings(page, ctx, delete=True)
    page.goto(f"{ctx.base_url}/admin/unified-settings?section=general")
    actual = bool((page.locator("input[name='selected_logo_filename'], #orgLogo-selected, #orgLogoFilename").get_attribute("value") or "").strip())
    if actual != enabled:
        raise AssertionError(f"Organization logo state should be {enabled}, but Settings reports {actual}.")
    ctx.note(f"Organization logo deliberately set to {'present' if enabled else 'absent'}.")


def _restore_org_logo(page, ctx, snapshot):
    if snapshot:
        # Put the original logo file back. Any temporary UAT logo file it replaces stays in
        # static/uploads as an orphan — that is preferred over the /unified-settings
        # "delete_logo" path, which also wipes activity owner-logo snapshots.
        _post_org_settings(
            page, ctx, logo_bytes=snapshot["buffer"], logo_name=snapshot["name"]
        )
    else:
        # There was no original logo. Use the real settings endpoint to clear it; this
        # unavoidably wipes activity owner-logo snapshots, so it is the last thing done.
        _post_org_settings(page, ctx, delete=True)
    ctx.note(f"Restored the pre-test organization logo state ({'present' if snapshot else 'absent'}).")


def _upload_activity_logo(page, ctx, activity_id):
    """Set both activity-logo stores exercised by customer surfaces.

    /activity/<id>/upload-logo backs passport/list fallbacks. The email editor's
    owner-logo upload backs the activity-specific identity used in sent emails.
    """
    page.goto(f"{ctx.base_url}/activity/{activity_id}/email-templates")
    page.wait_for_load_state("networkidle", timeout=15000)
    token = _csrf(page)
    with open(ACTIVITY_LOGO, "rb") as fixture:
        logo_bytes = fixture.read()

    response = page.request.post(
        f"{ctx.base_url}/activity/{activity_id}/upload-logo",
        multipart={
            "csrf_token": token,
            "logo_file": {
                "name": "uat_activity_logo.png", "mimeType": "image/png", "buffer": logo_bytes
            },
        },
    )
    _assert_response(response, "Uploading the activity logo used by passport pages")

    response = page.request.post(
        f"{ctx.base_url}/activity/{activity_id}/email-templates/save",
        multipart={
            "csrf_token": token,
            "single_template": "newPass",
            "newPass_owner_logo": {
                "name": "uat_activity_owner_logo.png", "mimeType": "image/png", "buffer": logo_bytes
            },
        },
    )
    _assert_response(response, "Uploading the activity-specific logo used by emails")
    payload = response.json()
    if not payload.get("success"):
        raise AssertionError(f"Activity email-logo upload was rejected: {payload!r}")
    ctx.note("Uploaded the activity logo through both real customer-facing logo workflows.")


def _assert_images_loaded(page, label, *, allow_cid=False):
    page.wait_for_timeout(750)
    broken = page.locator("img").evaluate_all(
        """(imgs, allowCid) => imgs.filter(img => {
          if (allowCid && (img.getAttribute('src') || '').startsWith('cid:')) return false;
          return !img.getAttribute('src') || !img.complete || img.naturalWidth === 0;
        }).map(img => img.getAttribute('src') || '<empty>')""",
        allow_cid,
    )
    if broken:
        raise AssertionError(f"[{label}] Broken or unloaded image(s): {broken}")


def _check_signup_form(page, ctx, activity_id, activity_name, has_org_logo, has_cover, viewport):
    fill_public_signup_form(page, ctx, activity_id, payment_method="interac")

    # Organization identity on the signup form header.
    org_img = page.locator("header .signup-logo")
    has_org_img = org_img.count() > 0
    if has_org_logo != has_org_img:
        raise AssertionError(
            f"[{viewport}] Signup form organization logo state wrong: "
            f"expected image={has_org_logo}, got image={has_org_img}."
        )
    if not has_org_logo:
        header = page.locator("header").first
        if not header.locator(".avatar, .fw-bold.text-dark").count():
            raise AssertionError(f"[{viewport}] Signup form did not show an organization logo fallback.")

    # Activity cover picture on the form pages.
    cover_images = page.locator('img[src*="uploads/activity_images/"]')
    if has_cover and not cover_images.count():
        raise AssertionError(f"[{viewport}] Signup form did not render the activity cover picture.")
    if not has_cover and cover_images.count():
        raise AssertionError(f"[{viewport}] Signup form unexpectedly rendered an activity picture.")
    if not has_cover:
        fallback_letter = page.locator("aside .display-1.text-primary")
        if not fallback_letter.count():
            raise AssertionError(f"[{viewport}] Signup form did not show its no-picture letter fallback.")
    _assert_images_loaded(page, f"signup form {viewport}")
    ctx.screenshot(page, f"signup_form_filled_{viewport}")


def _submit_signup(page, ctx):
    page.locator("#submit-button").click()
    page.wait_for_url("**/signup/thank-you/*", timeout=15000)
    signup_id = next((part for part in page.url.rstrip("/").split("/") if part.isdigit()), None)
    if not signup_id:
        raise AssertionError(f"Could not parse signup id from {page.url!r}.")
    return signup_id, page.url


def _check_thank_you(page, ctx, url, has_org_logo, viewport):
    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=15000)
    # Organization identity on public pages is the shared header in _public_base.html:
    # .mp-shop-header__brand renders an <img> when LOGO_FILENAME is set, otherwise the
    # avatar_initials() macro's .mp-avatar-initials. The old img.organization-logo /
    # .organization-logo-fallback classes don't exist in any template.
    actual_logo = page.locator(".mp-shop-header__brand img").count() > 0
    actual_fallback = page.locator(".mp-shop-header__brand .mp-avatar-initials").count() > 0
    if actual_logo != has_org_logo or actual_fallback == has_org_logo:
        raise AssertionError(
            f"[{viewport}] Signup confirmation organization fallback is wrong "
            f"(logo={actual_logo}, fallback={actual_fallback})."
        )
    _assert_images_loaded(page, f"signup confirmation {viewport}")
    ctx.screenshot(page, f"signup_confirmation_{viewport}")


def _find_pass_code(page, ctx, activity_id):
    page.goto(f"{ctx.base_url}/activity-dashboard/{activity_id}?q={config.TEST_EMAIL}")
    page.wait_for_load_state("networkidle", timeout=15000)
    row = page.locator(f'tr:has-text("{config.TEST_EMAIL}")').first
    row.wait_for(timeout=5000)
    # Row actions render as a[role="menuitem"] via macros/action_menu.html and only
    # populate once the trigger is clicked (a.dropdown-item predates that macro).
    row.locator('button[aria-label="Actions"]').first.click()
    page.wait_for_timeout(300)
    href = row.locator('[role="menuitem"]:has-text("View")').first.get_attribute("href")
    if not href:
        raise AssertionError("Approved signup has no passport View link.")
    return href.rstrip("/").split("/")[-1]


def _check_passport(page, ctx, pass_code, has_org_logo, has_activity_logo, has_cover, viewport):
    page.goto(f"{ctx.base_url}/pass/{pass_code}")
    page.wait_for_load_state("networkidle", timeout=15000)
    has_photo = page.locator(".pass-hero-photo").count() > 0
    has_contained_logo = page.locator(".pass-hero-contained img").count() > 0
    has_letter = page.locator(".pass-hero-letter").count() > 0
    expected = (
        (True, False, False) if has_cover else
        (False, True, False) if has_activity_logo else
        (False, False, True)
    )
    if (has_photo, has_contained_logo, has_letter) != expected:
        raise AssertionError(
            f"[{viewport}] Passport hero priority is wrong; expected {expected}, got "
            f"{(has_photo, has_contained_logo, has_letter)}."
        )
    org_image = page.locator("img.pass-hero-org-logo").count() > 0
    org_fallback = page.locator(".pass-hero-org-logo--fallback").count() > 0
    if org_image != has_org_logo or org_fallback == has_org_logo:
        raise AssertionError(f"[{viewport}] Passport organization-logo fallback is wrong.")
    qr = page.locator('img[alt="Code QR du passeport"]')
    if not qr.count():
        raise AssertionError(f"[{viewport}] Passport QR code is missing.")
    _assert_images_loaded(page, f"passport {viewport}")
    ctx.screenshot(page, f"passport_{viewport}")


def _check_email_previews(ctx, activity_id, has_cover):
    for template_type in ("signup", "newPass"):
        for viewport in ("desktop", "mobile"):
            with new_page(viewport=viewport) as page:
                login(page, base_url=ctx.base_url)
                page.goto(f"{ctx.base_url}/activity/{activity_id}/email-preview?type={template_type}")
                page.wait_for_load_state("networkidle", timeout=15000)
                photo_hero = page.locator('img[width="600"][height="184"]').count() > 0
                fallback_hero = page.locator('img[width="120"][height="120"]').count() > 0
                if has_cover and not photo_hero:
                    raise AssertionError(f"{template_type} preview did not use the activity cover photo.")
                if not has_cover and not fallback_hero:
                    raise AssertionError(f"{template_type} preview did not use the no-photo email fallback.")
                if not page.locator('img[width="56"][height="56"]').count():
                    raise AssertionError(f"{template_type} preview has no owner identity image/fallback.")
                _assert_images_loaded(page, f"{template_type} email preview {viewport}", allow_cid=True)
                ctx.screenshot(page, f"email_preview_{template_type}_{viewport}")


def _decoded_message_parts(message):
    html = None
    plain = None
    cid_parts = {}
    for part in message.walk():
        content_type = part.get_content_type()
        disposition = (part.get("Content-Disposition") or "").lower()
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        cid = (part.get("Content-ID") or "").strip("<>")
        if cid:
            cid_parts[cid] = f"data:{content_type};base64,{base64.b64encode(payload).decode()}"
        if "attachment" in disposition:
            continue
        charset = part.get_content_charset() or "utf-8"
        if content_type == "text/html":
            html = payload.decode(charset, errors="replace")
        elif content_type == "text/plain":
            plain = payload.decode(charset, errors="replace")
    if html:
        for cid, data_uri in cid_parts.items():
            html = html.replace(f"cid:{cid}", data_uri)
    return html, plain


def _wait_for_received_email(ctx, activity_name, subject_hint, label, not_before):
    """Optionally prove inbox receipt and render the received MIME message.

    IMAP is deliberately opt-in. Credentials live only in uattool/.env. Without
    them, the report records an explicit manual inbox obligation instead of
    falsely claiming that delivery was verified.
    """
    password = config.IMAP_PASSWORD
    if not password:
        ctx.note(
            f"MANUAL EMAIL CHECK REQUIRED: confirm the {label} email for {activity_name!r} "
            f"arrived at {config.TEST_EMAIL} and that its images/fallbacks look correct. "
            "Set UAT_IMAP_PASSWORD to automate receipt and received-HTML screenshots."
        )
        return

    deadline = time.monotonic() + config.IMAP_WAIT_SECONDS
    found = None
    while time.monotonic() < deadline and found is None:
        with imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT) as mailbox:
            mailbox.login(config.IMAP_USERNAME, password)
            mailbox.select(config.IMAP_FOLDER, readonly=True)
            since = datetime.fromtimestamp(not_before, tz=timezone.utc).strftime("%d-%b-%Y")
            status, data = mailbox.search(None, "SINCE", since)
            if status != "OK":
                raise AssertionError(f"IMAP search failed while waiting for the {label} email.")
            for message_id in reversed(data[0].split()[-40:]):
                status, raw = mailbox.fetch(message_id, "(RFC822)")
                if status != "OK" or not raw or not isinstance(raw[0], tuple):
                    continue
                candidate = email.message_from_bytes(raw[0][1])
                subject = str(make_header(decode_header(candidate.get("Subject", ""))))
                html, plain = _decoded_message_parts(candidate)
                searchable = " ".join((subject, html or "", plain or ""))
                if subject_hint.lower() in subject.lower() and activity_name in searchable:
                    found = (subject, html)
                    break
        if found is None:
            time.sleep(3)

    if found is None:
        raise AssertionError(
            f"The {label} email containing {activity_name!r} did not arrive within "
            f"{config.IMAP_WAIT_SECONDS} seconds."
        )
    subject, html = found
    ctx.note(f"Confirmed inbox receipt of {label}: {subject!r}.")
    if not html:
        ctx.note(f"Received {label} had no HTML part; visual screenshot was not possible.")
        return
    for viewport in ("desktop", "mobile"):
        with new_page(viewport=viewport) as page:
            page.set_content(html, wait_until="networkidle")
            _assert_images_loaded(page, f"received {label} {viewport}")
            ctx.screenshot(page, f"email_received_{label}_{viewport}")


def run_branding_case(ctx, *, case_id, org_logo, activity_logo, cover_photo):
    activity_name = scenario_name(
        "Branding Fallback",
        f"{case_id} O{int(org_logo)} A{int(activity_logo)} P{int(cover_photo)}",
    )
    snapshot = None
    snapshot_taken = False
    try:
        # Set global branding and build the fixture, then close this browser before opening
        # the logged-out customer contexts (Playwright's sync driver must not be nested).
        with new_page(viewport="desktop") as page:
            login(page, base_url=ctx.base_url)
            snapshot = _snapshot_org_logo(page, ctx)
            snapshot_taken = True
            _set_org_logo_state(page, ctx, org_logo)
            activity_id, activity_name, _ = create_minimal_activity(
                page,
                ctx,
                name=activity_name,
                workflow_type="approval_first",
                passport_type_name=f"UAT Branding {case_id}",
                description=(
                    f"UAT branding fallback case {case_id}: organization logo={org_logo}, "
                    f"activity logo={activity_logo}, cover photo={cover_photo}. Safe to archive."
                ),
                cover_image=COVER_IMAGE if cover_photo else None,
            )
            if activity_logo:
                _upload_activity_logo(page, ctx, activity_id)

        # Desktop is the submitted signup; mobile exercises the same filled form without
        # creating a duplicate participant/email.
        with new_page(viewport="mobile") as guest_mobile:
            _check_signup_form(
                guest_mobile, ctx, activity_id, activity_name, org_logo, cover_photo, "mobile"
            )

        signup_started = time.time()
        with new_page(viewport="desktop") as guest_desktop:
            _check_signup_form(
                guest_desktop, ctx, activity_id, activity_name, org_logo, cover_photo, "desktop"
            )
            signup_id, thank_you_url = _submit_signup(guest_desktop, ctx)
            _check_thank_you(guest_desktop, ctx, thank_you_url, org_logo, "desktop")

        with new_page(viewport="mobile") as guest_mobile:
            _check_thank_you(guest_mobile, ctx, thank_you_url, org_logo, "mobile")

        _wait_for_received_email(
            ctx, activity_name, "Registration Confirmed", "signup", signup_started
        )

        approval_started = time.time()
        with new_page(viewport="desktop") as page:
            login(page, base_url=ctx.base_url)
            page.goto(f"{ctx.base_url}/signup/approve-create-pass/{signup_id}")
            page.wait_for_load_state("networkidle", timeout=15000)
            assert_log_contains(page, "Signup Approved", base_url=ctx.base_url)
            assert_log_contains(page, activity_name, base_url=ctx.base_url)
            pass_code = _find_pass_code(page, ctx, activity_id)
            _check_passport(
                page, ctx, pass_code, org_logo, activity_logo, cover_photo, "desktop"
            )

        with new_page(viewport="mobile") as passport_mobile:
            _check_passport(
                passport_mobile, ctx, pass_code, org_logo, activity_logo, cover_photo, "mobile"
            )

        _check_email_previews(ctx, activity_id, cover_photo)
        _wait_for_received_email(
            ctx, activity_name, "Digital Pass", "passport", approval_started
        )
        ctx.note(
            f"Completed branding case {case_id}: org_logo={org_logo}, "
            f"activity_logo={activity_logo}, cover_photo={cover_photo}."
        )
    finally:
        # The organization logo is global tenant state. Always put it back, even when a
        # visual assertion, send, or inbox check fails halfway through the case.
        try:
            if snapshot_taken:
                with new_page(viewport="desktop") as restore_page:
                    login(restore_page, base_url=ctx.base_url)
                    _restore_org_logo(restore_page, ctx, snapshot)
        except Exception as restore_error:  # surface cleanup failure without hiding root cause
            ctx.note(f"URGENT CLEANUP WARNING: organization-logo restoration failed: {restore_error}")
            raise
