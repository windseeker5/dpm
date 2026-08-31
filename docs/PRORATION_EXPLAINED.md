# Proration Calculation — How Plan Changes Are Charged

## What is proration?

When a customer changes their plan mid-billing cycle, they should only pay for what they actually use. Proration calculates:

1. **Credit** for the unused portion of the old plan
2. **Charge** for the remaining portion of the new plan
3. **Net amount** = new charge minus credit

---

## Real Example: Solo Monthly ($20) to Club Monthly ($50)

### The facts

| Detail | Value |
|--------|-------|
| Current plan | Solo Monthly — $20/month |
| New plan | Club Monthly — $50/month |
| Billing cycle start | March 25, 2026 |
| Billing cycle end | April 25, 2026 |
| Upgrade date | April 12, 2026 |

### Step 1 — Count the days in the billing cycle

```
March 25 → April 25 = 31 days total
```

### Step 2 — Count days already used vs. days remaining

```
Days used:      March 25 → April 12 = 18 days
Days remaining: April 12 → April 25 = 13 days
```

### Step 3 — Calculate the "remaining ratio"

This is the percentage of the billing cycle that has NOT been used yet.

```
Remaining ratio = days remaining / total days
                = 13 / 31
                = 0.4194  (41.94%)
```

### Step 4 — Calculate the credit (unused old plan)

The customer already paid $20 for the full month. They only used 18 days.
They deserve a refund for the 13 days they won't use on Solo.

```
Credit = monthly price x remaining ratio
       = $20 x (13 / 31)
       = $20 x 0.4194
       = $8.39
```

### Step 5 — Calculate the new charge (prorated new plan)

The customer is switching to Club ($50/month) but only for the remaining 13 days,
not a full month. They'll pay a full $50 starting next billing cycle (April 25).

```
New charge = monthly price x remaining ratio
           = $50 x (13 / 31)
           = $50 x 0.4194
           = $20.97
```

### Step 6 — Calculate net amount charged today

```
Charged today = new charge - credit
              = $20.97 - $8.39
              = $12.58
```

### Summary

```
+--------------------------------------------------+
|  Confirm Plan Change                              |
|                                                   |
|  You are upgrading to Club (monthly).             |
|                                                   |
|  Credit (unused time)         -$8.39 CAD          |
|  New plan (prorated)         +$20.97 CAD          |
|  ────────────────────────────────────────          |
|  Charged today                $12.58 CAD          |
|                                                   |
|  Then on April 25: full $50.00 CAD charge         |
+--------------------------------------------------+
```

---

## Why the numbers change slightly each time

Stripe does NOT calculate by whole days. It calculates to the **exact second**.

If you check at 2:00 PM on April 12:
```
Seconds remaining = from April 12 14:00:00 to April 25 00:00:00
                  = 12 days + 10 hours = 1,076,400 seconds
Total seconds     = 31 days = 2,678,400 seconds
Ratio             = 1,076,400 / 2,678,400 = 0.40189 (40.19%)

Credit  = $20 x 0.40189 = $8.04
Charge  = $50 x 0.40189 = $20.09
Net     = $12.05
```

If you check 2 hours later at 4:00 PM:
```
Seconds remaining = 12 days + 8 hours = 1,069,200 seconds
Ratio             = 1,069,200 / 2,678,400 = 0.39921 (39.92%)

Credit  = $20 x 0.39921 = $7.98
Charge  = $50 x 0.39921 = $19.96
Net     = $11.98
```

**The ratio is always the same between credit and charge.** Only the remaining time changes. The amount is locked at the exact second you click "Confirm Upgrade".

---

## Other scenarios

### Same interval (monthly to monthly)

Only the **prorated difference** for the remaining days is charged.
Next billing date stays the same.

| From | To | Credit | New charge | Net |
|------|----|--------|------------|-----|
| Solo $20/mo | Club $50/mo | -$8.39 | +$20.97 | $12.58 |
| Solo $20/mo | Org $120/mo | -$8.39 | +$50.32 | $41.93 |
| Club $50/mo | Org $120/mo | -$20.97 | +$50.32 | $29.35 |

### Interval change (monthly to annual)

The full annual price is charged immediately, minus the credit for unused monthly time.
A new 12-month billing cycle starts today.

| From | To | Credit | New charge | Net |
|------|----|--------|------------|-----|
| Solo $20/mo | Solo $120/yr | -$8.39 | +$120.00 | $111.61 |
| Solo $20/mo | Club $300/yr | -$8.39 | +$300.00 | $291.61 |
| Solo $20/mo | Org $720/yr | -$8.39 | +$720.00 | $711.61 |

### Downgrade (higher to lower plan)

No charge. The current plan stays active until the end of the billing period.
The new (lower) plan starts on the next billing date.

| From | To | Charged today | Switch date |
|------|----|---------------|-------------|
| Club $50/mo | Solo $20/mo | $0 | April 25 |
| Org $120/mo | Solo $20/mo | $0 | April 25 |

---

## The formula

```
remaining_ratio = seconds_until_period_end / seconds_in_full_period

credit     = old_plan_price x remaining_ratio
new_charge = new_plan_price x remaining_ratio   (same interval)
           = new_plan_price                      (interval change)

charged_today = new_charge - credit
```

All amounts are in the subscription's currency (CAD for Minipass).
