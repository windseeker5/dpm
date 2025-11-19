# Simplified Subscription Management Plan

**Date:** November 18, 2025
**Version:** 1.0
**Status:** Ready for Implementation

---

## Overview

Transform `/current-plan` page into a clean subscription management page with unsubscribe functionality, using `.env` file for subscription metadata (no database changes).

---

## Research Findings

### Discovery: `/admin/subscription` Route Analysis

**Location:** `app.py` lines 9630-9691

**Status:** **INCOMPLETE PLACEHOLDER (20% Complete)**

This route was discovered during research and appears to be preparation code added in anticipation of Stripe subscription implementation. While the backend cancellation logic is solid, critical components are missing:

**What Exists:**
- Backend cancellation logic using `cancel_at_period_end=True`
- Proper Stripe API integration (`stripe.Subscription.modify()`)
- Error handling for Stripe API errors
- Authentication check

**What's Missing (Critical):**
- Template file (`templates/admin/subscription.html` does not exist)
- JSON file creation (no webhook or deployment script creates `subscription.json`)
- Navigation link (users cannot access this page)
- Subscription creation logic

**Conclusion:** This is placeholder code, well-written but incomplete. We will NOT use this route. Instead, we'll enhance the existing `/current-plan` route which is already working and has a template.

---

## Key Decisions

✅ **Use .env file** for subscription data (matches existing MINIPASS_TIER pattern)
✅ **Remove all upgrade buttons** - focus on current plan info and unsubscribe only
✅ **Show beta tester message** if no STRIPE_SUBSCRIPTION_ID exists
✅ **Keep existing /current-plan route** - the /admin/subscription route is just a placeholder stub
✅ **Use Stripe MCP** for actual subscription cancellation
✅ **No database changes** - keep it simple with environment variables

---

## Environment Variables Structure

### Existing Variables (Already Working)
```env
MINIPASS_TIER=2  # 1=Starter, 2=Professional, 3=Enterprise
```

### New Subscription Metadata (Added by website during deployment)
```env
# Stripe Integration
STRIPE_SUBSCRIPTION_ID=sub_xxxxx          # Required for unsubscribe
STRIPE_CUSTOMER_ID=cus_xxxxx              # Stripe customer reference
BILLING_FREQUENCY=annual                   # monthly or annual
SUBSCRIPTION_RENEWAL_DATE=2026-11-18      # ISO date format
PAYMENT_AMOUNT=300                         # Amount in CAD
```

### For Testing (Manual .env setup)
```env
# Beta Tester (No subscription)
MINIPASS_TIER=2
# No STRIPE_SUBSCRIPTION_ID = shows beta message

# Paid Subscriber (Has subscription)
MINIPASS_TIER=2
STRIPE_SUBSCRIPTION_ID=sub_test_12345
STRIPE_CUSTOMER_ID=cus_test_12345
BILLING_FREQUENCY=annual
SUBSCRIPTION_RENEWAL_DATE=2026-11-18
PAYMENT_AMOUNT=300
```

---

## Implementation Steps

### 1. Update `/current-plan` Route Logic

**File:** `app.py` (current location: lines 3004-3063)

**Changes Required:**
- Add POST method handling for unsubscribe action
- Read subscription metadata from environment variables
- Add Stripe cancellation logic using `stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)`
- Differentiate between paid subscribers vs beta testers

**New Helper Functions to Add:**
```python
def get_subscription_metadata():
    """Read subscription info from environment variables.

    Returns:
        dict: Subscription metadata including:
            - subscription_id: Stripe subscription ID (if exists)
            - customer_id: Stripe customer ID (if exists)
            - billing_frequency: 'monthly' or 'annual'
            - renewal_date: ISO date string
            - payment_amount: Amount in CAD
            - is_paid_subscriber: Boolean indicating if has subscription
    """
    return {
        'subscription_id': os.getenv('STRIPE_SUBSCRIPTION_ID'),
        'customer_id': os.getenv('STRIPE_CUSTOMER_ID'),
        'billing_frequency': os.getenv('BILLING_FREQUENCY', 'monthly'),
        'renewal_date': os.getenv('SUBSCRIPTION_RENEWAL_DATE'),
        'payment_amount': os.getenv('PAYMENT_AMOUNT'),
        'is_paid_subscriber': bool(os.getenv('STRIPE_SUBSCRIPTION_ID'))
    }

def cancel_subscription(subscription_id):
    """Cancel Stripe subscription at period end.

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        return True, "Subscription cancelled successfully. Access will continue until renewal date."
    except stripe.error.StripeError as e:
        return False, f"Stripe error: {str(e)}"
    except Exception as e:
        return False, f"Error cancelling subscription: {str(e)}"
```

**Updated Route Implementation:**
```python
@app.route('/current-plan', methods=['GET', 'POST'])
def current_plan():
    """Display current subscription plan and manage subscription"""
    if "admin" not in session:
        return redirect(url_for("login"))

    # Get tier info (existing logic)
    tier_info = get_tier_info()
    usage_info = get_activity_usage_display()

    # Get subscription metadata (new)
    subscription = get_subscription_metadata()

    # Handle unsubscribe POST request
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'cancel' and subscription['is_paid_subscriber']:
            success, message = cancel_subscription(subscription['subscription_id'])

            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')

            return redirect(url_for('current_plan'))

    return render_template('current_plan.html',
                         tier_info=tier_info,
                         usage_info=usage_info,
                         subscription=subscription)
```

---

### 2. Simplify Template

**File:** `templates/current_plan.html`

**Remove:**
- All upgrade tier cards (entire upgrade section)
- Fancy progress bars and animations
- "Upgrade to Enterprise" buttons
- Complex multi-column layouts

**Keep:**
- Current plan name and price
- Activity usage (X/Y activities)
- Clean, simple card design

**Add:**
- Renewal date display (if subscription exists)
- Billing frequency (Monthly/Annual)
- Unsubscribe button (if paid subscriber)
- Beta tester thank you message (if no subscription ID)
- Cancellation status banner (if already cancelled)

---

### 3. Page Variants

#### Variant A: Paid Subscriber (Has STRIPE_SUBSCRIPTION_ID)
```
┌─────────────────────────────────────────────┐
│ Current Subscription Plan                  │
├─────────────────────────────────────────────┤
│                                             │
│ Plan: Professional                          │
│ Price: $25/month (Annual billing)           │
│ Renews: November 18, 2026                   │
│                                             │
│ Activity Usage: 5/15 activities             │
│ ▓▓▓░░░░░░░ 33%                             │
│                                             │
│ ┌─────────────────────────────┐            │
│ │ Cancel Auto-Renewal          │            │
│ └─────────────────────────────┘            │
│ Access continues until Nov 18, 2026         │
│                                             │
└─────────────────────────────────────────────┘
```

#### Variant B: Beta Tester / No Subscription (No STRIPE_SUBSCRIPTION_ID)
```
┌─────────────────────────────────────────────┐
│ Current Plan                                │
├─────────────────────────────────────────────┤
│                                             │
│ Plan: Professional (Beta)                   │
│                                             │
│ Activity Usage: 5/15 activities             │
│ ▓▓▓░░░░░░░ 33%                             │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 🎉 Thank You for Beta Testing!          │ │
│ │                                         │ │
│ │ You're helping us build MiniPass.       │ │
│ │ We appreciate your support!             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

#### Variant C: Cancelled Subscription (cancel_at_period_end=True)
```
┌─────────────────────────────────────────────┐
│ ⚠️ Subscription Cancelled                   │
├─────────────────────────────────────────────┤
│                                             │
│ Plan: Professional                          │
│ Status: Will not auto-renew                 │
│ Access until: November 18, 2026             │
│                                             │
│ Activity Usage: 5/15 activities             │
│ ▓▓▓░░░░░░░ 33%                             │
│                                             │
│ Need to reactivate? Contact support.        │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Testing Plan

### Test Case 1: Beta Tester Environment
**Setup:**
```env
MINIPASS_TIER=2
# No STRIPE_SUBSCRIPTION_ID
```

**Expected Behavior:**
- ✅ Page loads successfully
- ✅ Shows tier name and activity limits
- ✅ Shows beta tester thank you message
- ✅ No unsubscribe button visible
- ✅ No renewal date shown

### Test Case 2: Paid Subscriber Environment
**Setup:**
```env
MINIPASS_TIER=2
STRIPE_SUBSCRIPTION_ID=sub_test_12345
STRIPE_CUSTOMER_ID=cus_test_12345
BILLING_FREQUENCY=annual
SUBSCRIPTION_RENEWAL_DATE=2026-11-18
PAYMENT_AMOUNT=300
```

**Expected Behavior:**
- ✅ Page loads successfully
- ✅ Shows tier name, price, billing frequency
- ✅ Shows renewal date
- ✅ Shows unsubscribe button
- ✅ Activity usage displayed correctly

### Test Case 3: Unsubscribe Flow
**Steps:**
1. Start with paid subscriber environment
2. Click "Cancel Auto-Renewal" button
3. Confirm dialog appears
4. Click confirm
5. POST request sent to `/current-plan` with action=cancel

**Expected Behavior:**
- ✅ Stripe API called with `cancel_at_period_end=True`
- ✅ Success flash message appears
- ✅ Page reloads showing cancelled status
- ✅ Unsubscribe button no longer visible
- ✅ "Access until [date]" message shown
- ✅ Activity usage still works

### Test Case 4: Stripe API Error Handling
**Simulation:** Invalid STRIPE_SUBSCRIPTION_ID

**Expected Behavior:**
- ✅ Error caught gracefully
- ✅ Error flash message shown
- ✅ User not logged out or crashed
- ✅ Can retry or contact support

### Test Case 5: Missing STRIPE_SECRET_KEY
**Setup:** Remove STRIPE_SECRET_KEY from .env

**Expected Behavior:**
- ✅ Error message shown
- ✅ Unsubscribe button disabled or hidden
- ✅ Clear message: "Subscription management unavailable"

---

## Website Integration (Future)

When the main website deploys a customer container, it should add subscription metadata to the `.env` file:

### Deployment Script Update
```python
# In main website's deployment webhook handler
def deploy_customer_container(customer_data, stripe_session):
    # ... existing deployment logic ...

    # Extract subscription data from Stripe session
    subscription_id = stripe_session.subscription
    customer_id = stripe_session.customer

    # Get subscription details
    subscription = stripe.Subscription.retrieve(subscription_id)
    renewal_date = datetime.fromtimestamp(subscription.current_period_end).date()

    # Determine billing frequency from price_id
    price_id = stripe_session.line_items.data[0].price.id
    billing_frequency = 'annual' if 'annual' in price_id else 'monthly'

    # Add to container .env file
    env_vars = {
        'MINIPASS_TIER': tier,
        'STRIPE_SUBSCRIPTION_ID': subscription_id,
        'STRIPE_CUSTOMER_ID': customer_id,
        'BILLING_FREQUENCY': billing_frequency,
        'SUBSCRIPTION_RENEWAL_DATE': renewal_date.isoformat(),
        'PAYMENT_AMOUNT': stripe_session.amount_total // 100,  # Convert cents to dollars
    }

    # Write to container .env file
    write_env_file(container_path, env_vars)
```

---

## Files to Modify

### 1. `app.py`
**Changes:** ~60-80 lines
- Add `get_subscription_metadata()` helper function
- Add `cancel_subscription()` helper function
- Update `/current-plan` route to handle GET and POST
- Add subscription data to template context

**Location:** Lines 3004-3063 (existing route)

### 2. `templates/current_plan.html`
**Changes:** Complete redesign (~100 lines)
- Remove all upgrade tier cards
- Simplify layout to single column
- Add conditional display based on subscription status
- Add unsubscribe form with confirmation
- Add beta tester message section
- Add cancelled subscription banner

**Current Location:** Working template exists

### 3. `.env`
**Changes:** Add test variables
```env
# For local testing - paid subscriber
STRIPE_SUBSCRIPTION_ID=sub_test_12345
STRIPE_CUSTOMER_ID=cus_test_12345
BILLING_FREQUENCY=annual
SUBSCRIPTION_RENEWAL_DATE=2026-11-18
PAYMENT_AMOUNT=300

# Stripe API key (if not already present)
STRIPE_SECRET_KEY=sk_test_...
```

---

## Files NOT Modified

✅ No database migrations needed
✅ No model changes (`models.py` unchanged)
✅ `/admin/subscription` route left as-is (unused stub, may be removed later)
✅ Navigation links stay the same (already points to `/current-plan`)
✅ No changes to tier enforcement logic

---

## Success Criteria

### User Experience
- ✅ Beta testers see thank you message (no subscription ID)
- ✅ Paid subscribers see renewal date and unsubscribe button
- ✅ Cancelled subscriptions show clear status banner
- ✅ All upgrade buttons removed (clean, focused UI)
- ✅ Single-page subscription management
- ✅ Mobile-responsive design

### Technical
- ✅ Unsubscribe calls Stripe API with `cancel_at_period_end=True`
- ✅ Proper error handling for Stripe API failures
- ✅ No crashes if STRIPE_SUBSCRIPTION_ID missing
- ✅ No database changes required
- ✅ Works with existing tier system
- ✅ Environment variable based (consistent with architecture)

### Business Logic
- ✅ Cancellation is graceful (access until period end)
- ✅ User cannot accidentally terminate immediately
- ✅ Confirmation dialog before cancellation
- ✅ Clear messaging about what cancellation means
- ✅ Beta testers have full access without payment

---

## Implementation Checklist

### Phase 1: Preparation (15 min)
- [ ] Read current `/current-plan` route code
- [ ] Read current `current_plan.html` template
- [ ] Review Stripe MCP documentation for subscription cancellation
- [ ] Set up test `.env` file with subscription variables

### Phase 2: Backend Development (45 min)
- [ ] Add `get_subscription_metadata()` function
- [ ] Add `cancel_subscription()` function
- [ ] Update `/current-plan` route to handle POST
- [ ] Add subscription data to template context
- [ ] Add error handling and flash messages
- [ ] Test with Python debugger

### Phase 3: Frontend Development (60 min)
- [ ] Simplify template layout (remove upgrade cards)
- [ ] Add subscription info display section
- [ ] Add unsubscribe button with form
- [ ] Add beta tester message section
- [ ] Add cancelled status banner
- [ ] Style with Tabler.io classes (consistent with existing)
- [ ] Add confirmation dialog JavaScript
- [ ] Test mobile responsiveness

### Phase 4: Testing (30 min)
- [ ] Test beta tester scenario (no subscription ID)
- [ ] Test paid subscriber scenario (has subscription ID)
- [ ] Test unsubscribe flow with test Stripe subscription
- [ ] Test error handling (invalid subscription ID)
- [ ] Test missing STRIPE_SECRET_KEY scenario
- [ ] Test on mobile device

### Phase 5: Documentation (15 min)
- [ ] Update this implementation plan with actual results
- [ ] Document any changes from original plan
- [ ] Add screenshots of final UI
- [ ] Update website deployment documentation

---

## Risk Mitigation

### Risk 1: Stripe API Key Not Available
**Impact:** Cannot test unsubscribe functionality
**Mitigation:** Add check for STRIPE_SECRET_KEY, show friendly error if missing
**Fallback:** Disable unsubscribe button if API key not configured

### Risk 2: Invalid Subscription ID
**Impact:** Unsubscribe fails
**Mitigation:** Proper error handling, user-friendly error messages
**Fallback:** Direct user to contact support

### Risk 3: Website Doesn't Set Environment Variables
**Impact:** All users appear as beta testers
**Mitigation:** Still functional, just shows beta message instead
**Rollout:** Update website deployment script before launching paid plans

### Risk 4: Template Breaks Existing Functionality
**Impact:** Current plan page unusable
**Mitigation:** Keep backup of current template, test thoroughly
**Rollback:** Restore original template if issues found

---

## Timeline

**Total Estimated Time: 2-3 hours**

- Preparation: 15 min
- Backend Development: 45 min
- Frontend Development: 60 min
- Testing: 30 min
- Documentation: 15 min
- Buffer: 15-45 min

**Suggested Schedule:**
- Day 1 (Session 1): Preparation + Backend Development
- Day 1 (Session 2): Frontend Development + Testing
- Day 2: Documentation + Final polish

---

## Future Enhancements

### Phase 2: Advanced Features (Post-MVP)
1. **Reactivate Subscription**
   - Button to undo cancellation before period end
   - Stripe API: `cancel_at_period_end=False`

2. **Subscription History**
   - Show past renewals
   - Payment history
   - Invoice downloads

3. **Upgrade/Downgrade**
   - Change tier without cancelling
   - Prorated billing
   - Immediate or at renewal

4. **Database Migration**
   - Move from .env to database table
   - Store subscription history
   - Better querying and reporting

5. **Email Notifications**
   - Confirmation email when cancelled
   - Reminder before subscription ends
   - Renewal confirmations

---

## Appendix

### A. Stripe API Reference

**Cancel at Period End:**
```python
stripe.Subscription.modify(
    'sub_xxxx',
    cancel_at_period_end=True
)
```

**Undo Cancellation:**
```python
stripe.Subscription.modify(
    'sub_xxxx',
    cancel_at_period_end=False
)
```

**Cancel Immediately:**
```python
stripe.Subscription.delete('sub_xxxx')
```
⚠️ **We do NOT use this** - too harsh for users

---

### B. Environment Variable Reference

| Variable | Format | Example | Required |
|----------|--------|---------|----------|
| MINIPASS_TIER | 1/2/3 | 2 | Yes |
| STRIPE_SUBSCRIPTION_ID | sub_xxxxx | sub_1ABC2DEF3 | For paid users |
| STRIPE_CUSTOMER_ID | cus_xxxxx | cus_ABC123DEF | For paid users |
| BILLING_FREQUENCY | monthly/annual | annual | For paid users |
| SUBSCRIPTION_RENEWAL_DATE | YYYY-MM-DD | 2026-11-18 | For paid users |
| PAYMENT_AMOUNT | Integer (CAD) | 300 | For paid users |
| STRIPE_SECRET_KEY | sk_test_... or sk_live_... | sk_test_51... | For API access |

---

### C. Template Context Reference

**Variables Passed to Template:**
```python
{
    'tier_info': {
        'name': 'Professional',
        'price': '$25/month',
        'activities': 15
    },
    'usage_info': {
        'current': 5,
        'limit': 15,
        'percentage': 33
    },
    'subscription': {
        'subscription_id': 'sub_xxxxx',
        'customer_id': 'cus_xxxxx',
        'billing_frequency': 'annual',
        'renewal_date': '2026-11-18',
        'payment_amount': '300',
        'is_paid_subscriber': True
    }
}
```

---

**END OF IMPLEMENTATION PLAN**

**Document Version:** 1.0
**Created:** November 18, 2025
**Last Updated:** November 18, 2025
**Status:** Ready for Implementation
