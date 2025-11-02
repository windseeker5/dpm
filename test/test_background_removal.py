#!/usr/bin/env python3
"""
Test script to verify background removal works on hero images
"""
import sys
import os
from PIL import Image
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from compileEmailTemplate import process_hero_image

def test_background_removal(image_path, output_path):
    """Test background removal on a single image"""
    print(f"\n{'='*60}")
    print(f"TESTING: {image_path}")
    print(f"{'='*60}\n")

    # Check original image
    original = Image.open(image_path)
    print(f"📷 ORIGINAL IMAGE:")
    print(f"   Size: {original.size}")
    print(f"   Mode: {original.mode}")

    # Process image
    print(f"\n🎨 PROCESSING (removing white background, NO padding)...")
    processed = process_hero_image(image_path, padding=0)

    print(f"\n✅ PROCESSED IMAGE:")
    print(f"   Size: {processed.size}")
    print(f"   Mode: {processed.mode}")

    # Calculate size reduction
    original_area = original.size[0] * original.size[1]
    processed_area = processed.size[0] * processed.size[1]
    reduction_pct = ((original_area - processed_area) / original_area) * 100

    print(f"\n📊 SIZE REDUCTION:")
    print(f"   Original area: {original_area} pixels ({original.size[0]}x{original.size[1]})")
    print(f"   Processed area: {processed_area} pixels ({processed.size[0]}x{processed.size[1]})")
    print(f"   Reduction: {reduction_pct:.1f}%")

    # Save output
    processed.save(output_path)
    print(f"\n💾 SAVED TEST OUTPUT TO: {output_path}")
    print(f"   View this image to verify white background is GONE!\n")

    # Verify it actually changed
    if processed.size == original.size:
        print(f"⚠️  WARNING: Image size unchanged! Background removal may have FAILED!")
        return False
    else:
        print(f"✅ SUCCESS: Image size changed, cropping appears to have worked!")
        return True

if __name__ == "__main__":
    # Test on signup image
    test_image = "signup/good-news.png"
    output_image = "test_cropped_signup.png"

    if os.path.exists(test_image):
        success = test_background_removal(test_image, output_image)

        print(f"\n{'='*60}")
        if success:
            print(f"✅ TEST PASSED: Background removal appears to work!")
            print(f"   Check {output_image} to visually confirm")
        else:
            print(f"❌ TEST FAILED: No cropping occurred!")
        print(f"{'='*60}\n")

        sys.exit(0 if success else 1)
    else:
        print(f"❌ ERROR: Test image '{test_image}' not found!")
        sys.exit(1)
