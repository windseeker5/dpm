# Real scenario names for UAT fixtures — supplied

These scenarios replace generic fixture names where they naturally fit. Every
created record still uses a unique UAT suffix, runs under
`kdresdell@gmail.com`, and avoids sending email to strangers.

## Scenario 1 — LHGI

- Activity name: LHGI
- Workflow type: payment-first (the supplied “payment” workflow)
- Passport type: Remplacant — $50 — 4 sessions
- Scheduling: none
- Used for: payment-first signup, passport creation/inheritance, check-in, and
  late-payment reminder rows

## Scenario 2 — Yoga

- Activity name: Yoga
- Workflow type: payment-first
- Passport type: Regulier — $200 — 25 sessions
- Products:
  - Tapis de yoga — $50
  - Legging — $70 — sizes S, M, L, XL
- Used for: the non-money shop/cart row

## Scenario 3

No scenario was supplied. Approval-first and identity-independent catalog rows
remain generic, as requested.

## Scenario 4 — Wing Foil Course

- Activity name: Wing Foil Course
- Workflow type: payment-first
- Passport type: Cours de 2h — $200 — 1 session
- Time slots: the next future Sunday, September 27, at 11am and 2pm
- Coaches: Ken and Jerome
- Used for: scheduled activity lifecycle, announcements, and surveys
- Coach names are stored and verified in the activity description because the
  current activity form has no dedicated coach field.

## Survey and announcements

- Wing Foil Course uses the compatible seeded French application survey.
- The test explicitly verifies that all 8 questions render.
- The Wing Foil Course announcement row sends email and, when
  `UAT_DISCORD_WEBHOOK_URL` is configured, posts to Discord.

## Naming decision

- [x] Only use scenario names where they fit naturally.
- [ ] Cycle every catalog row through the scenario names.
