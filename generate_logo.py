#!/usr/bin/env python3
"""
Generate Minipass logos using Google Gemini API
"""
import os
import requests
import base64
from datetime import datetime

# Load API key from environment
GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY')

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

def generate_image_with_gemini(prompt, variation_name):
    """
    Generate image using Gemini's imagen API
    Note: As of now, Gemini primarily focuses on text generation.
    For image generation, we'll use the text-to-image capabilities if available,
    or suggest using Imagen API directly.
    """
    print(f"\n{'='*60}")
    print(f"Generating: {variation_name}")
    print(f"{'='*60}")

    # Note: Gemini API doesn't have direct image generation in the free tier
    # We'll need to use a different approach
    print(f"\nPrompt:\n{prompt[:200]}...")

    # For now, let's save the prompts and provide instructions
    # In practice, you would use Imagen API or another image generation service

    return None

def main():
    print("Minipass Logo Generator")
    print("=" * 60)

    # Create output directory
    os.makedirs('static/logos', exist_ok=True)

    prompts = [
        ("main", MAIN_PROMPT),
        ("variation_1_qr_squares", VARIATION_1),
        ("variation_2_geometric_cut", VARIATION_2),
        ("variation_3_modular_grid", VARIATION_3)
    ]

    print("\nNOTE: Gemini API (free tier) primarily supports text generation.")
    print("For image generation, we have a few options:\n")
    print("1. Use Gemini in Google AI Studio web interface (supports image generation)")
    print("2. Use Imagen API (requires Google Cloud billing)")
    print("3. Use DALL-E, Midjourney, or similar services")
    print("4. Use your Groq API with a different model if it supports images")

    print("\n" + "="*60)
    print("RECOMMENDED APPROACH:")
    print("="*60)
    print("\nSince we have your API keys, let's try using:")
    print("- Gemini via Google AI Studio web interface (manual)")
    print("- Or implement a Python script using Pillow to create text-based logo")
    print("- Or use an external API like DALL-E, Replicate, or similar")

    print("\n" + "="*60)
    print("ALTERNATIVE: Create Simple Text Logo with Python")
    print("="*60)
    print("\nWould you like me to:")
    print("A) Create a Python script using Pillow to generate clean text logos")
    print("B) Provide you with the prompts to use manually in AI Studio")
    print("C) Try using an external API (Replicate, etc.)")

    # Save prompts to files for manual use
    for name, prompt in prompts:
        filename = f'static/logos/prompt_{name}.txt'
        with open(filename, 'w') as f:
            f.write(prompt)
        print(f"\nSaved: {filename}")

if __name__ == '__main__':
    main()
