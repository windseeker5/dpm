#!/usr/bin/env python3
"""Create a small test image for testing hero image resizing."""

from PIL import Image, ImageDraw
import os

# Create a small 300x300 smiley face image
size = 300
image = Image.new('RGB', (size, size), 'yellow')
draw = ImageDraw.Draw(image)

# Draw face outline
draw.ellipse([20, 20, size-20, size-20], outline='black', width=5)

# Draw eyes
eye_size = 30
draw.ellipse([size//3-eye_size//2, size//3, size//3+eye_size//2, size//3+eye_size], fill='black')
draw.ellipse([2*size//3-eye_size//2, size//3, 2*size//3+eye_size//2, size//3+eye_size], fill='black')

# Draw mouth (smile arc)
mouth_box = [size//3, size//2, 2*size//3, 3*size//4]
draw.arc(mouth_box, start=0, end=180, fill='black', width=8)

# Save the image
output_path = 'static/uploads/test_smiley_300x300.png'
image.save(output_path, 'PNG')
print(f"Created test image: {output_path} ({size}x{size} pixels)")

# Display image info
print(f"File size: {os.path.getsize(output_path)} bytes")