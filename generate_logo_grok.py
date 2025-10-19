#!/usr/bin/env python3
"""
Generate Minipass logos using Grok (xAI) Image Generation API
"""
import os
import requests
import base64
from datetime import datetime

# Load API key from environment
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Grok API endpoint for image generation
GROK_IMAGE_API = "https://api.x.ai/v1/images/generations"

# Prompts
MAIN_PROMPT = """Create a minimalist text-only logo for "minipass" - a SaaS platform for digital passes and QR codes.

STYLE REFERENCE: Stripe (note the geometric cut in the "S"), Linear, GitHub - clean wordmarks with subtle distinctive features

BRAND NAME: "minipass" (all lowercase, one word)

TYPOGRAPHY REQUIREMENTS:
- Modern geometric sans-serif font (similar to Inter, DM Sans, or Manrope)
- All lowercase: "minipass"
- Professional tech startup aesthetic
- Black text (#000000) on pure white background (#FFFFFF)
- Perfect letter spacing and kerning

SPECIAL "M" STYLING (Key Feature):
- The letter "m" should have a distinctive geometric treatment
- Inspired by QR code patterns: small geometric squares or pixel-like details integrated into the "m"
- Could be: geometric cuts, modular grid pattern, or subtle QR-code-inspired squares within the letter structure
- Keep it subtle and elegant - not overwhelming
- The "m" should still be readable but visually distinctive
- Think: Stripe's triangular "S" cut, but with a QR/digital pass theme for the "m"

STYLE:
- Clean, sharp, high contrast
- Slightly wide letter spacing for modern tech feel
- The special "m" should be the focal point but remain sophisticated

STRICT RULES:
- NO separate icons or graphics outside the text
- NO gradients or drop shadows
- NO taglines
- ONLY the word "minipass" with special "m" treatment

OUTPUT:
- High resolution (at least 2000px width)
- Centered on white background
- The "m" styling should be geometric and precise, not hand-drawn

Think: "Stripe's logo sophistication + QR code geometry for a digital pass platform" """

VARIATION_1 = MAIN_PROMPT + """

SPECIFIC STYLING FOR THIS VARIATION:
- The "m" incorporates 2-3 small squares (like QR code modules) integrated into the letter strokes
- Squares are negative space (cut-outs) or filled squares that create a pattern
- Positioned at the peaks or within the curves of the "m"
"""

VARIATION_2 = MAIN_PROMPT + """

SPECIFIC STYLING FOR THIS VARIATION:
- Clean geometric cut or slice through one of the "m" arches
- Creates a distinctive gap or angular feature
- Similar to how Stripe has the triangular cut in the "S"
- Suggests a "pass" or "ticket" being scanned
"""

VARIATION_3 = MAIN_PROMPT + """

SPECIFIC STYLING FOR THIS VARIATION:
- The "m" is constructed from a subtle modular grid
- Reminiscent of QR code pixel structure
- Still flows as a letter but has visible geometric construction
- Very minimal - just enough to suggest digital/technical
"""

def generate_image_with_grok(prompt, variation_name, num_images=1):
    """
    Generate image using Grok's image generation API
    """
    print(f"\n{'='*60}")
    print(f"Generating: {variation_name}")
    print(f"{'='*60}")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "n": num_images,  # Number of images to generate (1-10)
    }

    try:
        print(f"Sending request to Grok API...")
        response = requests.post(GROK_IMAGE_API, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Generated {len(result.get('data', []))} image(s)")

            # Save images
            os.makedirs('static/logos', exist_ok=True)

            for idx, image_data in enumerate(result.get('data', [])):
                # Grok returns image URLs
                image_url = image_data.get('url')
                if image_url:
                    # Download the image
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        filename = f'static/logos/{variation_name}_{idx+1}.jpg'
                        with open(filename, 'wb') as f:
                            f.write(img_response.content)
                        print(f"   Saved: {filename}")
                    else:
                        print(f"   ❌ Failed to download image from URL")

            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def main():
    print("🎨 Minipass Logo Generator using Grok API")
    print("=" * 60)
    print(f"API Key: {GROQ_API_KEY[:20]}...")
    print(f"Endpoint: {GROK_IMAGE_API}")
    print()

    # Create output directory
    os.makedirs('static/logos', exist_ok=True)

    prompts = [
        ("main_concept", MAIN_PROMPT),
        ("qr_squares", VARIATION_1),
        ("geometric_cut", VARIATION_2),
        ("modular_grid", VARIATION_3)
    ]

    print("⚠️  Cost: $0.07 per image")
    print(f"📊 Generating {len(prompts)} variations = ${len(prompts) * 0.07:.2f} total")
    print()

    # Generate each variation
    success_count = 0
    for name, prompt in prompts:
        if generate_image_with_grok(prompt, name):
            success_count += 1

    print("\n" + "="*60)
    print(f"✅ Successfully generated {success_count}/{len(prompts)} logo variations")
    print("="*60)
    print("\nImages saved in: static/logos/")
    print("\nNext steps:")
    print("1. Review the generated logos")
    print("2. Select your favorite")
    print("3. Process it (remove background, convert to SVG)")
    print("4. Integrate into your Flask app")

if __name__ == '__main__':
    main()
