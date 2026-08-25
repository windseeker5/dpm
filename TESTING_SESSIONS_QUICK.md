# Sessions feature — quick manual test

Admin: `kdresdell@gmail.com` / `admin123`. Customer role: separate/incognito window.
Always use `kdresdell@gmail.com` for any signup — real email gets sent.

1. **Create activity** → turn on "Let people choose a session" → add 2 dates × 2 times,
   6 spots → **Generate sessions** → expect **4 sessions**. Save, reopen, save again →
   still 4 (no duplicates).

2. **Sign up publicly** (incognito) on the signup link → must pick a session before
   submitting → submit with `kdresdell@gmail.com` → confirmation names the session.

3. **Approve the signup** as admin → check the email: QR code, "Votre séance:" line,
   "Voir mon passeport en ligne" button below the QR.

4. **Book more sessions** from the pass link in that email → credits go down 1 per
   booking, booked session drops out of the picker.

5. **Cancel a booked session** → credit comes back, seat reopens (reload signup page
   to confirm).

6. **Check-in test**:
   - customer with a session booked **today** → check in → **no credit deducted**
   - customer with **no** booking → check in → **credit deducted** (normal)

7. **Fill a session** (set spots to 1, book it) → shows **"Complet"**, greyed, not
   clickable, still visible.

8. **Delete a pending signup** → its seat reopens on the signup page.

9. **⭐ Regression — most important:** run a normal signup → approve → email → check-in
   on **LHGI** (sessions OFF). Must behave exactly as before, credit drops on check-in,
   no session picker anywhere — just the new pass-page button in the email.

Report a bug with: which step, what you did, expected vs. actual, screenshot if visual.
