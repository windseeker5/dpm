"""
Shared rendering for the activity-customizable part of an email (admin_message).

WHY THIS MODULE EXISTS
----------------------
`admin_message` is stored as *template source* — in `config/email_defaults.json` and, per
activity, in `Activity.email_templates`. Jinja does not recursively render a value, so
`{{ admin_message | safe }}` emits that source verbatim. The stored text therefore has to be
rendered in a second pass before it is injected into the email layout.

That rendering was spread across three places with three different contexts:

  * ``get_email_context``    -> the real pass, using the full merged context
  * ``notify_pass_event``    -> a second, narrower pass (pass_data / default_qt /
                                activity_list); a no-op in practice, because the text has
                                already been rendered by the time it runs
  * ``email_preview``        -> built ``pass_data`` locally for the owner/history blocks but
                                never put it in the context it passed on

The preview omission was the visible failure. ``{{ pass_data.user.name }}`` raised
UndefinedError, the bare ``except`` around the render swallowed it and fell back to the raw
source, so the template editor displayed Jinja tags as body text. The one tool for judging a
template never showed what was actually sent.

The latent failure was the fallback itself: *any* error in customized text silently degrades
to emitting template source to the customer. Combined with rendering DB-editable content
through a plain, unsandboxed ``jinja2.Template`` whose context holds live SQLAlchemy models,
that is both a robustness and a tenant-isolation concern in a multi-tenant app.

Every caller now builds its context with :func:`build_email_text_context` and renders with
:func:`render_email_text`, so the send path and the preview path cannot drift apart again.

VARIABLE NAMING
---------------
:data:`EMAIL_TEXT_VARIABLES` is the supported, documented set — flat scalars such as
``user_name`` and ``payment_email``. The nested ``pass_data.*`` / ``activity.*`` spellings
that older stored text uses are still populated for backward compatibility, so existing
per-activity customizations keep rendering, but new text should use the flat names.

SAFETY
------
This text comes out of the database and is editable by activity owners, so it is rendered
in a Jinja ``SandboxedEnvironment`` — a customized template cannot reach through an object
into application internals. Undefined names render empty instead of raising: a typo in a
customized template must never take down a signup or a passport send.
"""

from types import SimpleNamespace

from jinja2.sandbox import SandboxedEnvironment
from jinja2 import ChainableUndefined


# The supported variable set, as (name, description). Surfaced in the docs and available
# for the customization UI to show as a placeholder cheat-sheet.
EMAIL_TEXT_VARIABLES = [
    ("user_name", "Recipient's full name"),
    ("user_email", "Recipient's email address"),
    ("user_phone", "Recipient's phone number"),
    ("activity_name", "Name of the activity"),
    ("activity_location", "Formatted address of the activity, when set"),
    ("organization_name", "Your organization's name"),
    ("amount", "Amount as a number, e.g. for '%.2f'|format(amount)"),
    ("amount_display", "Amount preformatted for display, e.g. 50,00 $"),
    ("credits_remaining", "Credits left on the passport"),
    ("is_paid", "True when the passport is paid"),
    ("payment_email", "Address the customer should send payment to"),
    ("pass_code", "The passport's code"),
    ("pass_url", "Link to the customer's online passport"),
    ("session_count", "Number of sessions the customer has booked"),
    ("sessions", "List of booked session labels"),
    ("signup_code", "Reference code for a payment-first signup"),
    ("requested_amount", "Amount requested at signup, preformatted"),
]


# ChainableUndefined so an unknown path (`{{ a.b.c }}`) renders empty rather than raising.
_ENV = SandboxedEnvironment(undefined=ChainableUndefined, autoescape=False)


def _ns(**kwargs):
    """A plain attribute bag. Only scalars go in — never a live SQLAlchemy model."""
    return SimpleNamespace(**kwargs)


def build_email_text_context(
    *,
    activity=None,
    user=None,
    pass_data=None,
    signup=None,
    organization_name=None,
    payment_email=None,
    pass_url=None,
    sessions=None,
    extra=None,
):
    """Build the complete variable context for rendering stored email text.

    Every argument is optional so the same builder serves the passport path, the signup
    path and the preview. Anything unknown is left empty rather than omitted, so
    ``{% if payment_email %}`` is a meaningful test instead of an accident.

    Returns a plain dict of scalars (plus two compatibility namespaces); no ORM objects
    are exposed to the sandbox.
    """
    from utils import get_setting

    # --- identity -----------------------------------------------------------------
    if user is None and pass_data is not None:
        user = getattr(pass_data, "user", None)
    if user is None and signup is not None:
        user = getattr(signup, "user", None)

    user_name = getattr(user, "name", "") or ""
    user_email = getattr(user, "email", "") or ""
    user_phone = getattr(user, "phone_number", "") or ""

    # --- activity -----------------------------------------------------------------
    if activity is None and pass_data is not None:
        activity = getattr(pass_data, "activity", None)
    activity_name = getattr(activity, "name", "") or ""
    activity_location = getattr(activity, "location_address_formatted", "") or ""

    # --- organization / payment ---------------------------------------------------
    if organization_name is None:
        organization_name = get_setting("ORG_NAME", "minipass")
    if payment_email is None:
        # Same resolution the signup path already used: an explicit display address wins,
        # otherwise fall back to the mailbox that actually receives payments.
        display_email = get_setting("DISPLAY_PAYMENT_EMAIL")
        payment_email = display_email or get_setting("MAIL_USERNAME", "")

    # --- passport -----------------------------------------------------------------
    amount = getattr(pass_data, "sold_amt", None)
    if amount is None and signup is not None:
        amount = getattr(signup, "requested_amount", None)
    amount = float(amount or 0)

    credits_remaining = getattr(pass_data, "uses_remaining", None)
    if credits_remaining is None:
        credits_remaining = getattr(pass_data, "games_remaining", 0) or 0

    is_paid = bool(getattr(pass_data, "paid", False))
    pass_code = getattr(pass_data, "pass_code", "") or ""

    sessions = list(sessions or [])

    context = {
        "user_name": user_name,
        "user_email": user_email,
        "user_phone": user_phone,
        "activity_name": activity_name,
        "activity_location": activity_location,
        "organization_name": organization_name or "",
        "amount": amount,
        # French formatting, matching utils._fr_money and the money() macro in
        # templates/email/components.html — one email must never show both "$50.00" and
        # "50,00 $", which it did when this was the only US-formatted value left.
        "amount_display": f"{amount:.2f}".replace(".", ",") + " $",
        "credits_remaining": credits_remaining,
        "is_paid": is_paid,
        "payment_email": payment_email or "",
        "pass_code": pass_code,
        "pass_url": pass_url or "",
        "session_count": len(sessions),
        "sessions": sessions,
        # Populated by the signup path only; present-but-empty elsewhere so that
        # `{% if signup_code %}` is a valid test in any template.
        "signup_code": "",
        "requested_amount": "",
        # Pre-existing names used by the survey/announcement text.
        "default_qt": 0,
        "activity_list": "",
    }

    # --- backward compatibility ---------------------------------------------------
    # Older stored text addresses `pass_data.user.name`, `pass_data.uses_remaining`,
    # `pass_data.activity.name` and `activity.location_address_formatted`. Mirror those
    # spellings as inert scalar namespaces so existing customizations keep working.
    context["activity"] = _ns(
        name=activity_name,
        location_address_formatted=activity_location,
    )
    context["pass_data"] = _ns(
        user=_ns(name=user_name, email=user_email, phone_number=user_phone),
        activity=context["activity"],
        sold_amt=amount,
        uses_remaining=credits_remaining,
        games_remaining=credits_remaining,
        paid=is_paid,
        pass_code=pass_code,
    )

    if extra:
        # "activity" and "pass_data" were just converted to inert SimpleNamespace copies
        # above specifically so no live SQLAlchemy model reaches the sandbox — callers pass
        # the whole assembled context dict as `extra` for convenience, and it commonly still
        # carries the *live* ORM objects under these same keys. Never let those two keys be
        # reintroduced here: doing so previously let a customized template call
        # `pass_data.query` / `activity.query` (SandboxedEnvironment only blocks dunder
        # access, not ordinary method calls) and enumerate other activities' records.
        context.update({k: v for k, v in extra.items() if k not in ("activity", "pass_data")})

    return context


def render_email_text(raw, context):
    """Render one stored text field (admin_message) against ``context``.

    Never raises: a broken customized template degrades to the unrendered source rather
    than aborting the email that carries the customer's passport.
    """
    if not raw:
        return ""
    try:
        return _ENV.from_string(raw).render(**context)
    except Exception as e:  # noqa: BLE001 - a bad customization must not block a send
        print(f"⚠️  Email text render failed, falling back to raw source: {e}")
        return raw
