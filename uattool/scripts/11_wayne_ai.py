"""Row 11 — Wayne AI.

Drives the real Wayne chat UI at /chatbot/ (templates/analytics_chatbot_simple.html,
static/js/wayne-chat.js) with a representative subset of the question set from
docs/WAYNE_GUIDE_FR.md, covering several of its categories (priorities,
signups/payments, passports, finances, surveys) rather than the full list —
this is a smoke test, not exhaustive coverage.

UI mechanics (read from the template + JS, not guessed):
  - First question of a session: textarea #wayne-start-input inside
    #wayne-start-form (large "welcome" composer), submitted by its button
    `#wayne-start-form .wayne-send` (or Enter).
  - Once #wayne-welcome is hidden and #wayne-conversation is shown, every
    subsequent question uses textarea #wayne-chat-input inside
    #wayne-chat-form, submitted by `#wayne-chat-form .wayne-send`.
  - Both forms POST via fetch to /chatbot/ask (JSON), and wayne-chat.js
    appends a new `<article class="wayne-message wayne-message-wayne">`
    (or `wayne-message-user` for the echoed question) into #wayne-messages,
    inserted right before the `#wayne-typing` indicator. A failed/erroring
    response additionally gets the `wayne-message-error` class
    (see addMessage(..., isError) in wayne-chat.js) — that's the reliable
    signal for "Wayne crashed", as opposed to a legitimate "I don't know
    that skill yet" answer, which is still returned with success=true and
    therefore never carries wayne-message-error (see _message() in
    wayne/routes.py: "unsupported"/"fallback"/"out_of_scope" are normal,
    non-error replies).
"""

from lib.browser import login, new_page

# A representative cross-section of docs/WAYNE_GUIDE_FR.md's categories:
# daily priorities, signups/payments, passports/credits, finances, surveys.
QUESTIONS = [
    "Qu'est-ce qui nécessite mon attention aujourd'hui?",
    "Qui n'a pas encore payé son inscription?",
    "Quels passeports ont encore des crédits?",
    "Quelle activité a généré le plus de revenus?",
    "Résume les réponses aux sondages.",
]


def _ask(page, ctx, question, timeout_ms=30000):
    """Type `question` into whichever composer is currently active, submit it,
    wait for a new wayne-message-wayne bubble to appear, and return its text.
    """
    conversation_hidden = page.locator("#wayne-conversation").is_hidden()
    if conversation_hidden:
        input_sel, form_sel = "#wayne-start-input", "#wayne-start-form"
    else:
        input_sel, form_sel = "#wayne-chat-input", "#wayne-chat-form"

    before_count = page.locator(".wayne-message-wayne").count()

    page.fill(input_sel, question)
    page.locator(f"{form_sel} .wayne-send").click()

    # Wait for the typing indicator to appear then clear, and for a new
    # wayne-message-wayne bubble to land.
    page.wait_for_function(
        "(args) => document.querySelectorAll(args.sel).length > args.before",
        arg={"sel": ".wayne-message-wayne", "before": before_count},
        timeout=timeout_ms,
    )
    # wait_for_selector defaults to state="visible", but "#wayne-typing[hidden]" describes
    # an element that is by definition NOT visible, so the default can never be satisfied.
    # state="attached" is the right check: the indicator exists and carries [hidden].
    page.wait_for_selector("#wayne-typing[hidden]", state="attached", timeout=timeout_ms)

    bubble = page.locator(".wayne-message-wayne").last
    is_error = "wayne-message-error" in (bubble.get_attribute("class") or "")
    text = bubble.locator(".wayne-message-content").inner_text().strip()

    ctx.note(f"Wayne Q: {question!r} -> A ({'ERROR' if is_error else 'ok'}): {text[:200]!r}")

    if is_error:
        raise AssertionError(f"Wayne returned an error bubble for {question!r}: {text!r}")
    if not text:
        raise AssertionError(f"Wayne returned an empty answer for {question!r}")

    return text


def run(ctx):
    # --- desktop pass: ask most of the question set ---
    with new_page(viewport="desktop") as page:
        login(page, base_url=ctx.base_url)
        page.goto(f"{ctx.base_url}/chatbot/")

        for question in QUESTIONS[:3]:
            _ask(page, ctx, question)

        ctx.screenshot(page, "wayne_chat_desktop")

    # --- mobile pass: fresh session, remaining questions, confirm the UI
    #     itself (not just the skill logic) works below the 768px breakpoint ---
    with new_page(viewport="mobile") as page:
        login(page, base_url=ctx.base_url)
        page.goto(f"{ctx.base_url}/chatbot/")

        for question in QUESTIONS[3:]:
            _ask(page, ctx, question)

        ctx.screenshot(page, "wayne_chat_mobile")
