#!/usr/bin/env python3
"""
Save all cropped hero images as visible PNG files for verification
"""
import sys
import os
from compileEmailTemplate import process_hero_image

# List of hero images to process
hero_images = [
    ("signup/good-news.png", "signup/good-news_CROPPED.png"),
    ("newPass/hero_new_pass.png", "newPass/hero_new_pass_CROPPED.png"),
    ("paymentReceived/currency-dollar.png", "paymentReceived/currency-dollar_CROPPED.png"),
    ("redeemPass/hand-rock.png", "redeemPass/hand-rock_CROPPED.png"),
    ("latePayment/thumb-down.png", "latePayment/thumb-down_CROPPED.png"),
    ("survey_invitation/sondage.png", "survey_invitation/sondage_CROPPED.png"),
]

print("=" * 70)
print("SAVING ALL CROPPED HERO IMAGES AS PNG FILES")
print("=" * 70)
print()

for original_path, cropped_path in hero_images:
    if os.path.exists(original_path):
        print(f"Processing: {original_path}")

        # Process image (remove white background, no padding)
        cropped_img = process_hero_image(original_path, padding=0)

        # Save as PNG
        cropped_img.save(cropped_path)

        # Get file sizes for comparison
        original_size = os.path.getsize(original_path)
        cropped_size = os.path.getsize(cropped_path)

        print(f"  ✅ Saved to: {cropped_path}")
        print(f"  📊 File size: {original_size:,} bytes → {cropped_size:,} bytes")
        print()

print("=" * 70)
print("✅ ALL CROPPED IMAGES SAVED!")
print("=" * 70)
print()
print("Now open these *_CROPPED.png files in an image viewer")
print("to verify the white background is actually gone!")
print()
