# minipass Shop — Feature Proposal

## Recommendation

Add a simple public shop to every minipass customer site:

`https://customer.minipass.me/shop`

The shop should show activities and products in one place. Keep the first version intentionally small and easy to manage.

## Main Goal

An organization should be able to start selling in a few minutes without learning ecommerce software.

## Simple User Experience

### For the organization

1. Open **Settings → Shop**.
2. Turn on **Enable my shop**.
3. Choose which activities appear in the shop.
4. Add products with a name, photo, price, and available quantity.
5. Share the `/shop` link.
6. Manage new orders from one simple order list.

### For the customer

1. Visit `/shop`.
2. Browse **Activities** and **Products**.
3. Select an item.
4. Enter contact information.
5. Pay by Interac or credit card.
6. Receive a confirmation email.

## Recommended First Version

Include:

- Shop on/off setting
- Public `/shop` page using the organization’s branding
- Existing activities linked to their signup forms
- Simple physical products
- Optional sizes, such as small, medium, and large
- Basic stock quantity
- Pickup only
- Interac and Stripe payments
- Order confirmation emails
- Admin order list
- Order statuses: awaiting payment, paid, ready, picked up, and cancelled

Do not include yet:

- Shipping
- Discount codes
- Gift cards
- Customer accounts
- Complex taxes
- Products and activities in the same cart
- Equipment rentals

## Best-Practice Structure

Keep activities and products separate behind the scenes because they work differently. Display them together only in the public shop.

Every purchase should create an order with a unique reference such as `MP-ORD-0001234`. Customers include this reference with an Interac transfer so minipass can match the payment safely.

Product names and prices should be saved on the order so old orders remain correct after a product changes.

## Delivery Plan

### Phase 1 — Shopfront

- Add the shop setting.
- Create `/shop`.
- Show selected activities.
- Link activities to the existing signup process.

### Phase 2 — Product Sales

- Add product management.
- Add sizes and basic stock.
- Add checkout and orders.
- Add Interac matching and Stripe payment.
- Add confirmation emails and the admin order list.

### Phase 3 — Improvements Based on Demand

- Shopping cart
- Taxes
- Shipping
- Discounts
- Refund tools
- Customer order history

### Phase 4 — Equipment Rentals

Build rentals separately because they require rental dates, availability, deposits, pickup, returns, late fees, and damage tracking.

## Product Positioning

Do not try to replace Shopify. Position the feature as:

> One simple place for local organizations to sell activities, passes, products, and eventually rentals—with Interac built in.

## Final Recommendation

Start with activities, simple pickup products, and one-item checkout. This version is useful, easy to understand, and realistic to build. Add carts, shipping, and rentals only after customers request them.
