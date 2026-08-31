# Minipass Testing Guide

## Golden rule

**Test every implemented UI flow with pi's `browser-tools` against the real local app at `http://localhost:5000`.** Do not rely only on test-client scripts, database copies, or static previews.

Pi's browser tools connect to a real Chrome instance through the Chrome DevTools Protocol. Inspect the DOM first, interact with the real page, and use screenshots for visual confirmation. Playwright is optional, not required.

Scripts can silently target the wrong database and do not exercise real templates, JavaScript, CSRF, or session behavior.

## Dev environment

- Flask app: `app/app.py`
- Database: `app/instance/minipass.db`
- Local admin login: `kdresdell@gmail.com` / `admin123`

## Test data rules

- **Always use `kdresdell@gmail.com`** for any User, Passport, or Signup created during testing. The app sends real SMTP mail; fake domains bounce and can flag the sending account.
- **Verify cleanup with a direct SQLite query**, not just through the app/ORM. ORM identity-map caching across multiple requests can make a deletion look like it failed (or succeeded) when it didn't.

## Test artifacts

Save screenshots, scripts, and images in `test/` — never in the main `app/` folder.

## Unit tests

```bash
cd app
source venv/bin/activate
python -m py_compile app.py utils.py models.py api/settings.py decorators.py
python -m compileall .
```

## End-to-end smoke test — sessions feature

This covers the Book Session flow. Open two browser contexts: one logged in as admin, one private/incognito as a customer.

### 1. Create a sessions activity

1. As admin: **Activities → New Activity**.
2. Name: `Wingfoil Beginner`.
3. In the **Sessions** section, turn on "Let people choose a session when they sign up".
4. Add dates, times, and spots; click **Generate sessions**.
5. Add a passport type (e.g. `5 Lessons Pack`, price `250`, sessions included `5`).
6. Save, reopen, save again — verify sessions do not duplicate.

### 2. Sign up as a customer

1. Copy the signup link from the passport type row.
2. Open it in a **private/incognito** window.
3. Verify the session picker shows spots.
4. Verify submitting without choosing a session is rejected.
5. Choose a session, complete signup with email `kdresdell@gmail.com`.
6. Verify the thank-you page names the chosen session and the spot count drops.

### 3. Approve and check the email

1. As admin: **Signups**, approve the signup.
2. Check the inbox.
3. Email must contain: QR code, "Votre séance:" with date/time, "Voir mon passeport en ligne" button below the QR, and "Réservez vos prochaines séances au même endroit."

### 4. Book more sessions as the customer

1. Open the passport link from the email.
2. Verify credits remaining and the **Mes séances** card.
3. Book additional sessions; verify credits drop and the booked session is excluded from the dropdown.
4. Cancel a booking; verify the credit is returned and the spot is freed.

### 5. Check-in as admin

1. Book a session for today on the customer's passport.
2. As admin, scan/click **Check In**.
3. Verify the message says no credit was used (already paid at booking) and the session badge changes to "Présence confirmée".

### 6. Fill a session

1. Set a session to 1 spot.
2. Sign up for it.
3. Reload the public signup page — the session must show "Complet", greyed out, still visible.

### 7. Reject a signup

1. Create another pending signup on any session.
2. As admin, **Delete** the signup.
3. Verify the seat is freed.

### 8. Regression test — sessions off

1. Open an activity with sessions **off** (e.g. `Hockey du midi LHGI`).
2. Sign up, approve, check the email, redeem the passport.
3. Verify behavior is identical to before the sessions feature: credit drops on check-in, no session picker, no "Réservez vos prochaines séances" line.

## Email testing

- Render check: `python test/render_all.py`
- Real SMTP: `python test/send_real_email_preview.py --reset-fixture`
- Browser preview: `http://localhost:5000/activity/<id>/email-preview?type=newPass`

## What to report when something breaks

- Part/step number.
- What you did (which button/link).
- Expected vs actual result.
- Screenshot for visual issues, error text for crashes.
