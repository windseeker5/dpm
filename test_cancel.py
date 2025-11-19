#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv()

# Import app functions
from app import cancel_subscription, get_subscription_metadata, get_subscription_details

# Test get_subscription_metadata
meta = get_subscription_metadata()
print("=" * 60)
print("SUBSCRIPTION METADATA (from .env):")
print("=" * 60)
print(f"is_paid_subscriber: {meta['is_paid_subscriber']}")
print(f"subscription_id: {meta['subscription_id']}")
print(f"customer_id: {meta['customer_id']}")
print()

# Test get_subscription_details
details = get_subscription_details()
print("=" * 60)
print("SUBSCRIPTION DETAILS (live from Stripe API):")
print("=" * 60)
if details:
    print(f"ID: {details['id']}")
    print(f"Status: {details['status']}")
    print(f"cancel_at_period_end: {details['cancel_at_period_end']}")
else:
    print("ERROR: Could not fetch subscription details")
print()

# Test cancel_subscription
if meta['subscription_id']:
    print("=" * 60)
    print(f"TESTING CANCEL FOR: {meta['subscription_id']}")
    print("=" * 60)
    success, message = cancel_subscription(meta['subscription_id'])
    print(f"Success: {success}")
    print(f"Message: {message}")
