"""Single source of truth for the UAT catalog.

CATALOG.md is *generated* from this list (see lib/catalog.py) — don't hand-edit
the table in CATALOG.md, edit a row here instead. This is deliberate: when Ken
reads a run report and says "row 7 is wrong, it should do X", the fix is a
one-line edit to that row's `description` (and the matching script), then
regenerate.

Fields:
  order        str, matches the script filename prefix and run order
  script       filename in scripts/, or None for a [MANUAL] catalog-only row
  area         short section name
  description  plain-English description of what the script does
  credentials  admin/user login used
  email        email address used for any User/Passport/Signup/etc. created
  viewport     "desktop+mobile" | "desktop" | "mobile" | "n/a"
  verifies     what it checks, including which Activity Log entry it expects
  money        True if this step moves real money (gated behind --confirm-money)
  manual       True if this row is never run by run_uat.py at all
"""

CATALOG = [
    dict(
        order="00", script="00_preflight.py", area="Preflight",
        description="Log in as admin once per viewport (desktop, then mobile), confirm kdc.minipass.me is reachable and answers as expected, and confirm the browser logged no JS console error or uncaught exception during login/dashboard load; refuses to let any money-tier script run unless --confirm-money was passed.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop+mobile",
        verifies="Successful redirect to /dashboard after login at both viewports, with a screenshot per viewport; no JS console errors or uncaught exceptions logged during the process.",
        money=False, manual=False,
    ),
    dict(
        order="01", script="01_activity_with_photo.py", area="Activity lifecycle",
        description="Create the realistic Wing Foil Course scenario with a cover photo (AI/stock picker plus direct upload), payment-first workflow, a 'Cours de 2h' passport at $200 for 1 session, coaches Ken and Jerome named in the description, and two bookable sessions on the next Sunday September 27 at 11am and 2pm. Also tests capacity, Stripe/shop toggles, edit, and archive.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop+mobile",
        verifies="Activity Log shows 'Activity Created' and an 'Activity' row with the photo persisted after edit/archive.",
        money=False, manual=False,
    ),
    dict(
        order="01b", script="01b_activity_no_photo.py", area="Activity lifecycle",
        description="Create an activity with NO cover photo (approval-first workflow this time), confirm the app falls back to its default image everywhere instead of a broken image tag.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop+mobile",
        verifies="Activity Log shows 'Activity Created'; no broken <img> on the activity page or dashboard card.",
        money=False, manual=False,
    ),
    dict(
        order="02", script="02_signup_payment_first.py", area="Signup",
        description="Create the realistic LHGI payment-first scenario with a 'Remplacant' passport at $50 for 4 sessions, then sign up as Ken through the public form. This fixture is not quantity-limited, so it checks the signup's 'Awaiting Payment' status instead of a seat count.",
        credentials="none (public signup form)", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Activity Log shows 'Signup Submitted' (the real log text); the new signup shows the 'Awaiting Payment' badge on the activity dashboard.",
        money=False, manual=False,
    ),
    dict(
        order="02b", script="02b_signup_approval_first.py", area="Signup",
        description="Create a fresh approval-first fixture activity (independent of row 01b, no photo) and sign up as a real customer; approve it as admin.",
        credentials="admin approves as kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Activity Log shows 'Signup Approved' (real log text confirmed exactly).",
        money=False, manual=False,
    ),
    dict(
        order="03", script="03_passport_admin_create.py", area="Passport",
        description="Create the LHGI payment-first scenario with a 'Remplacant' passport at $50 for 4 sessions, then have the admin issue that passport directly to Ken (not through signup).",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="desktop",
        verifies="Activity Log shows 'Passport Created'; QR code renders on the passport page.",
        money=False, manual=False,
    ),
    dict(
        order="03b", script="03b_passport_inheritance.py", area="Passport",
        description="Create two LHGI payment-first activities using the 'Remplacant' $50/4-session passport: issue Ken a passport on activity A, then configure activity B to inherit A's passports and confirm the same passport is usable on B.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="desktop",
        verifies="Activity B's passport table shows the same pass_code tagged 'Inherited' — checked at the UI level (matching pass_code, single occurrence), not by a direct DB query.",
        money=False, manual=False,
    ),
    dict(
        order="04", script="04_checkin_qr.py", area="Check-in / QR",
        description="Create an LHGI 'Remplacant' passport ($50, 4 sessions), then check it in via the admin 'Check In' action and confirm one session is consumed. The physical-camera QR scan cannot be automated headlessly, so this uses the real pass-code fallback route. Mobile is prioritized for this door flow.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="mobile+desktop",
        verifies="Activity Log shows the passport was redeemed; remaining credits/sessions on the passport page decrement by one.",
        money=False, manual=False,
    ),
    dict(
        order="05", script="05_announcements_discord.py", area="Announcements & Discord",
        description="Create the Wing Foil Course scenario ($200 'Cours de 2h', 1 session; coaches Ken and Jerome), issue its subscriber passport only to Ken at kdresdell@gmail.com, configure the real Discord webhook, then send both email and Discord announcements. Without UAT_DISCORD_WEBHOOK_URL, email still runs and Discord is reported as skipped.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Ken is the activity subscriber; Activity Log shows 'Announcement Sent'; email is addressed to kdresdell@gmail.com and arrives with images; message appears in the real Discord channel.",
        money=False, manual=False,
    ),
    dict(
        order="06", script="06_shop_nonmoney.py", area="Shop (non-money paths)",
        description="Create the realistic Yoga payment-first shop scenario: 'Regulier' passport at $200 for 25 sessions, a $50 tapis de yoga, and $70 leggings in S/M/L/XL. Browse the shop and build a mixed cart containing all three (leggings in XL), then stop before checkout.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Yoga, mat, and leggings appear in /shop; S/M/L/XL sizes render; selected XL persists in the cart; mixed-cart total is $320.",
        money=False, manual=False,
    ),
    dict(
        order="07", script="07_surveys.py", area="Surveys",
        description="Create the Wing Foil Course scenario and send its supplied 8-question application survey to Ken, submit desktop and mobile responses, view results, and export them. Uses the compatible seeded French 8-question template because the default English template has a known incompatible schema.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var) (respondent uses the emailed survey link)", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="All 8 questions render; Activity Log shows the survey send; two SurveyResponses are recorded; export is non-empty.",
        money=False, manual=False,
    ),
    dict(
        order="08", script="08_data_export.py", area="Data export",
        description="Download the signups, financial report, user-contacts, passports, and survey-results exports; confirm each downloaded file is non-empty and parses.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop",
        verifies="Each export file exists, is non-empty, and has the expected header row.",
        money=False, manual=False,
    ),
    dict(
        order="09", script="09_activity_log_crosscheck.py", area="Activity Log cross-check",
        description="Final consolidated pass over /activity-log: confirm every non-money log type this suite can produce (Activity Created, Signup Submitted/Approved, Passport Created/Redeemed, Announcement Sent, etc.) has at least one matching entry, to catch anything an individual script's inline assertion missed. Money-only types (Stripe/Interac payment) are noted, never failed on, since rows 90/91 may not have run.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop",
        verifies="No non-money-dependent log type is missing from the log.",
        money=False, manual=False,
    ),
    dict(
        order="10", script="10_outbound_doc_links.py", area="Outbound doc links",
        description="Crawl Settings (and anywhere else the app links out) for links to minipass.me/docs, request each one, confirm HTTP 200 — including the one Ken already flagged as broken.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop",
        verifies="Every discovered outbound doc link returns HTTP 200.",
        money=False, manual=False,
    ),
    dict(
        order="11", script="11_wayne_ai.py", area="Wayne AI",
        description="Ask Wayne the question set from docs/WAYNE_GUIDE_FR.md through the real chat UI, confirm it answers rather than erroring.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="desktop+mobile",
        verifies="Each question gets a non-error response; entries land in QueryLog.",
        money=False, manual=False,
    ),
    dict(
        order="12", script="12_late_payment_reminders.py", area="Late payment reminders",
        description="Create an unpaid Interac signup for the LHGI payment-first scenario ('Remplacant', $50, 4 sessions), then trigger the real reminder-send hook. Same-day signups are too new for the default 15-day reminder filter, so this verifies the trigger is logged rather than claiming that the fixture received email.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="kdresdell@gmail.com", viewport="desktop",
        verifies="Activity Log shows 'Manual late payment reminder test by {admin}'. Does NOT verify actual reminder-email delivery (see note) — a known limitation, not a bug in the app.",
        money=False, manual=False,
    ),
    dict(
        order="13a", script="13a_branding_b1.py", area="Branding & fallback matrix",
        description="B1 — run signup → approval → passport with an organization logo, activity-specific logo, and activity cover picture. Capture the public form, confirmation, passport, signup email, and passport email at desktop and mobile sizes.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="All three images follow their intended priority; no image is broken; both workflow emails are sent. With optional UAT_IMAP_PASSWORD, also proves inbox receipt and captures received HTML; otherwise reports a manual inbox check. Restores the original organization logo even after failure.",
        money=False, manual=False,
    ),
    dict(
        order="13b", script="13b_branding_b2.py", area="Branding & fallback matrix",
        description="B2 — organization logo and activity-specific logo present, but NO activity cover picture. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Signup uses its no-cover fallback; passport falls back to the activity logo; emails use the generic no-photo hero while retaining activity identity. Checks sends/optional receipt and restores organization settings.",
        money=False, manual=False,
    ),
    dict(
        order="13c", script="13c_branding_b3.py", area="Branding & fallback matrix",
        description="B3 — organization logo and activity cover picture present, but NO activity-specific logo. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Cover picture leads signup/passport/email hero treatment; activity identity falls back to the organization logo. Checks broken images, sends/optional receipt, and safe restoration.",
        money=False, manual=False,
    ),
    dict(
        order="13d", script="13d_branding_b4.py", area="Branding & fallback matrix",
        description="B4 — organization logo present, with NO activity-specific logo and NO cover picture. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Signup/passport/email no-picture fallbacks render while organization identity remains branded. Checks broken images, sends/optional receipt, and safe restoration.",
        money=False, manual=False,
    ),
    dict(
        order="13e", script="13e_branding_b5.py", area="Branding & fallback matrix",
        description="B5 — NO organization logo, with activity-specific logo and cover picture present. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Organization identity uses its letter fallback while activity branding remains complete. Checks broken images, sends/optional receipt, and safe restoration.",
        money=False, manual=False,
    ),
    dict(
        order="13f", script="13f_branding_b6.py", area="Branding & fallback matrix",
        description="B6 — NO organization logo and NO cover picture, with an activity-specific logo present. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Signup/email use no-cover treatment; passport falls back to the activity logo; organization identity uses its generated fallback. Checks sends/optional receipt and restoration.",
        money=False, manual=False,
    ),
    dict(
        order="13g", script="13g_branding_b7.py", area="Branding & fallback matrix",
        description="B7 — NO organization logo and NO activity-specific logo, with an activity cover picture present. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Cover picture remains intact while both owner-identity locations use their fallbacks. Checks broken images, sends/optional receipt, and safe restoration.",
        money=False, manual=False,
    ),
    dict(
        order="13h", script="13h_branding_b8.py", area="Branding & fallback matrix",
        description="B8 — complete fallback case: NO organization logo, NO activity-specific logo, and NO cover picture. Exercise the complete signup → approval → passport and email workflow.",
        credentials="admin setup/approval as kdresdell@gmail.com; public signup is logged out", email="kdresdell@gmail.com", viewport="desktop+mobile",
        verifies="Every customer surface renders its intended generated/letter fallback with no broken image. Checks both workflow sends/optional receipt and always restores the tenant's original organization-logo state.",
        money=False, manual=False,
    ),
    dict(
        order="90", script="90_production_stripe_live.py", area="[REAL MONEY] Stripe payment",
        description="Create a $1 product and a $1 activity, drive Stripe Checkout up to the payment form, then PAUSE for Ken to type his own real card number and submit ($2.00 total). Resumes to verify the resulting records AND that the money reached the financial report.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var) (+ Ken's own card, entered by hand)", email="kdresdell@gmail.com", viewport="desktop",
        verifies="StripeTransaction + Passport/Order created; Activity Log shows the payment. Financial report moves by the exact amounts and nothing else moves: the $1 activity lands in ACCOUNTS RECEIVABLE (Stripe income is booked pending until payout, and the passport itself is excluded from the views), the $1 product lands in CASH RECEIVED on a 'Boutique' row. Report page and CSV export agree on every bucket.",
        money=True, manual=False,
    ),
    dict(
        order="91", script="91_production_interac_live.py", area="[REAL MONEY] Interac payment",
        description="Buy ONE mixed cart — a $2.00 activity passport plus a $1.00 shop product, $3.00 total — then PAUSE for Ken to send himself a single real e-transfer for that amount to the inbox kdc.minipass.me monitors. Triggers the matcher behind /test-payment-bot-now and verifies the payment splits correctly across the books.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var) (+ one real $3.00 e-transfer, sent by hand)", email="kdresdell@gmail.com", viewport="desktop",
        verifies="EbankPayment result = MATCHED; Activity Log shows the cart code. Before payment the $3.00 sits in ACCOUNTS RECEIVABLE with cash untouched; after payment it MOVES to CASH RECEIVED with the total unchanged (catching double-counting). The split is checked: the activity row gets exactly $2.00 and the product's $1.00 goes to 'Boutique', never to the activity. Product line present in both the report page and the CSV export; report page and CSV agree on every bucket.",
        money=True, manual=False,
    ),
    dict(
        order="92", script=None, area="[MANUAL] Backup / restore",
        description="Generate a backup and, separately, restore one — done by hand by Ken on kdc.minipass.me. Never scripted: restoring overwrites the tenant's real database in place.",
        credentials="kdresdell@gmail.com (password via UAT_ADMIN_PASSWORD env var)", email="n/a", viewport="n/a",
        verifies="Manual — no automated check.",
        money=False, manual=True,
    ),
]
