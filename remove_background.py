#!/usr/bin/env python3
"""
Background removal script using rembg library.
Removes background from images and saves as PNG with transparency.

Usage: python remove_background.py input_image.jpg [output_image.png]
"""

import sys
import os
from PIL import Image
from rembg import remove

def remove_background(input_path, output_path=None):
    """
    Remove background from image and save as PNG with transparency.
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path for output PNG (optional)
    
    Returns:
        str: Path to output file
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.dirname(input_path)
            output_path = os.path.join(output_dir, f"{base_name}_no_bg.png")
        
        # Ensure output has .png extension
        if not output_path.lower().endswith('.png'):
            output_path = os.path.splitext(output_path)[0] + '.png'
        
        # Read input image
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        # Remove background
        print(f"Processing {input_path}...")
        output_data = remove(input_data)
        
        # Save as PNG with transparency
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)
        
        print(f"Background removed successfully!")
        print(f"Output saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python remove_background.py input_image.jpg [output_image.png]")
        print("Example: python remove_background.py photo.jpg photo_no_bg.png")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = remove_background(input_path, output_path)
    
    if result:
        print(f"\n✅ Success! Transparent PNG saved to: {result}")
    else:
        print("\n❌ Failed to process image")
        sys.exit(1)

if __name__ == "__main__":
    main()