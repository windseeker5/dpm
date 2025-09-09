#!/usr/bin/env python3
"""Direct test of the resize_hero_image function"""

import os
from utils import resize_hero_image

# Test the resize function directly
TEST_IMAGE_PATH = "static/uploads/test_smiley_300x300.png"

if os.path.exists(TEST_IMAGE_PATH):
    with open(TEST_IMAGE_PATH, 'rb') as f:
        image_data = f.read()
    
    print(f"Testing resize_hero_image function directly...")
    print(f"Original image size: {len(image_data)} bytes")
    
    result = resize_hero_image(image_data, 'newPass')
    
    if isinstance(result, tuple):
        resized_data, message = result
        print(f"Function returned tuple: ({type(resized_data)}, '{message}')")
        
        if resized_data:
            print(f"Resized data size: {len(resized_data)} bytes")
            
            # Save and check dimensions
            test_output = "test_resized_output.png"
            with open(test_output, 'wb') as f:
                f.write(resized_data)
            
            try:
                from PIL import Image
                with Image.open(test_output) as img:
                    width, height = img.size
                    print(f"Resized dimensions: {width}x{height}")
                    
                    if width == 1408 and height == 768:
                        print("✅ Resize function works correctly!")
                    else:
                        print(f"❌ Wrong dimensions: expected 1408x768, got {width}x{height}")
                        
            except ImportError:
                print("PIL not available to check dimensions")
            
            # Clean up
            os.remove(test_output)
            
        else:
            print(f"❌ Resize failed: {message}")
    else:
        print(f"Function returned: {type(result)} - {result}")
else:
    print(f"Test image not found: {TEST_IMAGE_PATH}")