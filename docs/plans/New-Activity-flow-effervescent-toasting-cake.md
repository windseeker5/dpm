# Plan: Activity Workflow Types & Quantity Limits

## Overview

Add two major features to Minipass:
1. **Workflow Types** - "approval-first" vs "payment-first" activity flows
2. **Quantity Limits** - Limited capacity events with session-based tracking

## Feature Summary

### Workflow Types

| Workflow | Use Case | Flow |
|----------|----------|------|
| **Approval-first** (default) | Hockey leagues, skill-based activities | Signup → Admin approval → Passport created → User pays |
| **Payment-first** | Concerts, events, no vetting needed | Signup (choose qty) → User pays → Passport auto-created |

### Quantity Limits

- Admin sets max session capacity (e.g., 80 seats)
- Signup form shows quantity selector (capped at remaining)
- Shows "X spots left" (optional)
- Auto-blocks signups when sold out

---

## Model Changes

### Activity (new fields)
```python
# Workflow configuration
workflow_type = db.Column(db.String(50), default="approval_first")  # "approval_first" | "payment_first"
allow_quantity_selection = db.Column(db.Boolean, default=False)     # Show qty picker on signup

# Quantity limits
is_quantity_limited = db.Column(db.Boolean, default=False)
max_sessions = db.Column(db.Integer, nullable=True)                 # Total capacity
show_remaining_quantity = db.Column(db.Boolean, default=False)      # Display "X left" on form
```

### Signup (new fields)
```python
requested_sessions = db.Column(db.Integer, default=1)    # User's chosen quantity
requested_amount = db.Column(db.Float, default=0.0)      # Calculated total (price × qty)
```

---

## Logic Changes

### 1. Signup Form (`/signup/<activity_id>`)

**File:** `app/app.py` (lines 2093-2147)
**Template:** `templates/signup_form.html`

Changes:
- Add quantity dropdown (1 to remaining capacity)
- Dynamic price calculation: `unit_price × quantity`
- If `is_quantity_limited`: cap dropdown at available spots
- If sold out: show "SOLD OUT" message, disable form
- Store `requested_sessions` and `requested_amount` in Signup record

**Capacity calculation:**
```python
def get_remaining_capacity(activity_id):
    total_sold = db.session.query(func.sum(Passport.uses_remaining))\
        .filter(Passport.activity_id == activity_id).scalar() or 0
    return activity.max_sessions - total_sold
```

### 2. Activity Edit Form

**File:** `app/app.py` (activity edit route)
**Template:** `templates/activity_form.html` or similar

Add new fields:
- Workflow type selector (radio buttons)
- "Allow quantity selection on signup" checkbox
- "Enable quantity limit" checkbox
- Max sessions input (shown when limit enabled)
- "Show remaining quantity" checkbox

### 3. Payment Matching Extension

**File:** `app/utils.py` (lines 1247+)
**Function:** `match_gmail_payments_to_passes()`

Current: Matches payments to **unpaid Passports**
New: For payment-first activities, also match to **Signups without passports**

```python
# After checking unpaid passports, for payment-first activities:
if not matched and activity.workflow_type == "payment_first":
    unmatched_signups = Signup.query.filter(
        Signup.activity_id == activity_id,
        Signup.passport_id == None,
        Signup.requested_amount == payment_amount
    ).all()
    # Match by name + amount
    # If matched: auto-create passport
```

### 4. Auto-Passport Creation

**New function in:** `app/utils.py`

```python
def auto_create_passport_from_signup(signup, payment_record):
    """Create passport automatically when payment matches a signup"""
    passport = Passport(
        pass_code=generate_pass_code(),
        user_id=signup.user_id,
        activity_id=signup.activity_id,
        passport_type_id=signup.passport_type_id,
        uses_remaining=signup.requested_sessions,
        sold_amt=signup.requested_amount,
        paid=True,
        paid_date=datetime.utcnow(),
        marked_paid_by="minipass-bot@system"
    )
    signup.passport_id = passport.id
    signup.paid = True
    # Send passport email automatically
```

---

## Migration Strategy

1. **Existing activities**: Set `workflow_type = "approval_first"` (no behavior change)
2. **Database migration**: Add columns with safe defaults
3. **No data loss**: Existing signups/passports unaffected

---

## Files to Modify

| File | Changes |
|------|---------|
| `app/models.py` | Add new fields to Activity and Signup models |
| `app/app.py` | Modify signup route, activity edit route |
| `app/templates/signup_form.html` | Add quantity selector, sold out UI |
| `app/templates/activity_form.html` | Add workflow/limit configuration fields |
| `app/utils.py` | Extend payment matching, add auto-passport function |
| `migrations/upgrade_production_database.py` | Add migration task for new columns |

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing activities | Default to approval_first, existing flows unchanged |
| Payment matching complexity | New logic only triggers for payment_first activities |
| Overbooking if concurrent signups | Check capacity on form submit (not just form load) |
| Amount mismatch payments | Continue current behavior: notify admin, don't auto-match |

---

## Verification Plan

### Unit Tests
- [ ] Capacity calculation returns correct remaining sessions
- [ ] Signup blocked when capacity reached
- [ ] Payment matching finds correct signup for payment-first activities
- [ ] Auto-passport created with correct session count

### Manual Testing (MCP Playwright)
1. Create payment-first activity with 10 session limit
2. Submit signup for 3 sessions → verify signup created with requested_sessions=3
3. Simulate payment match → verify passport auto-created with uses_remaining=3
4. Submit signups until capacity reached → verify "SOLD OUT" displayed
5. Existing approval-first activity → verify no behavior change

---

## Implementation Order

1. **Models** - Add new fields to Activity and Signup
2. **Migration** - Create database migration task
3. **Activity form** - Add configuration fields for workflow/limits
4. **Signup form** - Add quantity selector and sold out logic
5. **Payment matching** - Extend to check signups for payment-first
6. **Auto-passport** - Create passport on payment match
7. **Testing** - Unit tests + Playwright integration tests
