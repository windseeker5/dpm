"""
Direct test of hero image replacement logic
"""
import os
import sys

# Test the exact logic from utils.py
activity_id = 4

print(f"Testing Activity ID: {activity_id}")

# Check path construction
hero_image_path = os.path.join("static/uploads", f"{activity_id}_hero.png")
print(f"Hero path: {hero_image_path}")

# Check existence
if os.path.exists(hero_image_path):
    print(f"✅ File exists: {hero_image_path}")
    hero_data = open(hero_image_path, "rb").read()
    print(f"✅ File size: {len(hero_data)} bytes")
    
    # This should replace the default image
    inline_images = {'good-news': b'default_image_data'}
    print(f"Before: good-news size = {len(inline_images['good-news'])} bytes")
    
    inline_images['good-news'] = hero_data
    print(f"After: good-news size = {len(inline_images['good-news'])} bytes")
    print(f"✅ Replacement successful!")
else:
    print(f"❌ File does NOT exist: {hero_image_path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Directory listing:")
    if os.path.exists("static/uploads"):
        for f in os.listdir("static/uploads"):
            if "hero" in f:
                print(f"  - {f}")