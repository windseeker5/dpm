import os
import re
import json
import base64
import sys
import time
import traceback
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageChops


def process_hero_image(image_path: str, padding: int = 0, target_size: int = 400):
    """
    Process hero images into a standard 400x400 RGBA square canvas:
    1. Crop white/near-white border from source image
    2. Convert near-white pixels to transparent
    3. Scale-to-fit cropped content within 400x400 RGBA canvas (centered)

    Output is always RGBA PNG -- transparent background prevents white box in dark mode.
    The HTML uses width="152" height="auto" so the 400px canvas renders at ~152x152 (2.6x retina).

    Args:
        image_path: Path to the image file
        padding: Unused (kept for backward compatibility)
        target_size: Canvas size in pixels (default: 400)

    Returns:
        PIL Image object (RGBA, target_size x target_size)
    """
    try:
        import numpy as np

        # Open image; convert to RGB for white-border detection
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_array = np.array(img)

        # Near-white threshold: catches off-white AI-generator backgrounds
        white_threshold = 240
        is_white = (img_array[:, :, 0] > white_threshold) & \
                   (img_array[:, :, 1] > white_threshold) & \
                   (img_array[:, :, 2] > white_threshold)

        # Find bounding box of non-white content
        rows_with_content = np.where(~is_white.all(axis=1))[0]
        cols_with_content = np.where(~is_white.all(axis=0))[0]

        if len(rows_with_content) > 0 and len(cols_with_content) > 0:
            top = rows_with_content[0]
            bottom = rows_with_content[-1] + 1
            left = cols_with_content[0]
            right = cols_with_content[-1] + 1
            img_cropped = img.crop((left, top, right, bottom))
            print(f"   Cropped from {img.size} to {img_cropped.size} (removed white border)")
        else:
            img_cropped = img
            print(f"   No non-white content found, using original image")

        # Convert to RGBA and make near-white pixels transparent
        img_rgba = img_cropped.convert('RGBA')
        rgba_array = np.array(img_rgba)
        near_white = (rgba_array[:, :, 0] > white_threshold) & \
                     (rgba_array[:, :, 1] > white_threshold) & \
                     (rgba_array[:, :, 2] > white_threshold)
        rgba_array[near_white, 3] = 0  # Set alpha=0 (transparent)
        img_rgba = Image.fromarray(rgba_array, 'RGBA')
        transparent_count = int(near_white.sum())
        print(f"   Converted {transparent_count} near-white pixels to transparent")

        # Scale-to-fit within target_size x target_size, preserving aspect ratio
        img_rgba.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        fitted_width, fitted_height = img_rgba.size

        # Create transparent canvas and center the scaled image
        canvas = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        offset_x = (target_size - fitted_width) // 2
        offset_y = (target_size - fitted_height) // 2
        canvas.paste(img_rgba, (offset_x, offset_y), mask=img_rgba)

        print(f"   Scaled to {fitted_width}x{fitted_height}, centered on {target_size}x{target_size} RGBA canvas")
        return canvas

    except Exception as e:
        print(f"Warning: Could not process image {image_path}: {e}")
        print(f"Returning blank {target_size}x{target_size} RGBA canvas")
        import traceback
        traceback.print_exc()
        # Return a transparent canvas rather than crashing
        return Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))


def compile_email_template_to_folder(template_name: str, update_original: bool = False, url_mode: bool = False):
    """
    Compile email template with comprehensive logging and error handling

    Args:
        template_name: Name of the template to compile (e.g., 'newPass', 'signup')
        update_original: If True, updates the pristine original folder (for production deployment)
                        If False, only updates compiled folder (for development/testing)
        url_mode: If True, produces URL-referenced HTML (Phase 3 hybrid hosted images).
                  Hero images are replaced with {{ hero_image_url }}, interac logo with
                  its static hosted URL. inline_images.json is still written (needed by
                  the /hero-image/ route). If False (default), produces CID-based HTML.
    """
    try:
        print(f"\U0001f4e7 Starting compilation of '{template_name}'")
        if url_mode:
            print(f"\U0001f310 IMAGE MODE: URL-based (Phase 3 hybrid hosted images)")
        else:
            print(f"\U0001f4ce IMAGE MODE: CID inline (classic)")
        if update_original:
            print(f"\U0001f504 MODE: Production Deployment (updating pristine original)")
        else:
            print(f"\U0001f6e0\ufe0f  MODE: Development (compiled only, original preserved)")

        start_time = time.time()

        source_dir = os.path.abspath(template_name)
        target_dir = os.path.abspath(f"{template_name}_compiled")
        original_dir = os.path.abspath(f"{template_name}_original")

        print(f"\U0001f4c2 Source path: {source_dir}")
        print(f"\U0001f4c2 Target path: {target_dir}")
        print(f"\U0001f4c2 Original path: {original_dir}")

        # Verify source directory exists
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Source directory '{source_dir}' does not exist")

        # Create both compiled and original directories
        os.makedirs(target_dir, exist_ok=True)
        print(f"\u2705 Created/verified target directory: {target_dir}")

        # Check if original version already exists (to preserve pristine version)
        original_exists = os.path.exists(original_dir)
        if not original_exists:
            os.makedirs(original_dir, exist_ok=True)
            print(f"\u2705 Created original directory: {original_dir}")
        else:
            print(f"\u2139\ufe0f  Original directory already exists: {original_dir}")

        source_html_path = os.path.join(source_dir, "index.html")
        target_html_path = os.path.join(target_dir, "index.html")
        inline_images_path = os.path.join(target_dir, "inline_images.json")

        # Original paths (only created if doesn't exist)
        original_html_path = os.path.join(original_dir, "index.html")
        original_images_path = os.path.join(original_dir, "inline_images.json")

        # Verify source HTML file exists
        if not os.path.exists(source_html_path):
            raise FileNotFoundError(f"Source HTML file '{source_html_path}' does not exist")

        print(f"\U0001f4c4 Reading source HTML: {source_html_path}")
        with open(source_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        source_size = len(html)
        print(f"\U0001f4cf Source HTML size: {source_size} characters")

        if source_size == 0:
            raise ValueError(f"Source HTML file '{source_html_path}' is empty")

        cid_map = {}

        # In URL mode: strip dead {% set logo_url = 'cid:logo_image' %} line (Phase 3)
        if url_mode:
            html = re.sub(r'\{%\s*set logo_url\s*=\s*\'cid:logo_image\'\s*%\}\n?', '', html)

        # Match <img src="..."> tags (only file-path references, not cid: or http: already)
        matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        # Filter to local file references only
        matches = [m for m in matches if not m.startswith('cid:') and not m.startswith('http')]
        print(f"\U0001f5bc\ufe0f  Processing {len(matches)} images")

        for match in matches:
            asset_path = os.path.join(source_dir, os.path.basename(match))

            if os.path.exists(asset_path):
                cid = os.path.splitext(os.path.basename(asset_path))[0]
                filename = os.path.basename(asset_path).lower()

                try:
                    # Check if this is a hero image (should be preprocessed)
                    is_hero_image = any(hero_name in filename
                                      for hero_name in ['hero', 'good-news', 'currency-dollar',
                                                       'hand-rock', 'thumb-down', 'sondage'])

                    # Check if this is the interac logo
                    is_interac = 'interac' in filename

                    if is_hero_image:
                        print(f"\U0001f3a8 Preprocessing hero image (auto-crop, transparent canvas)...")
                        img_processed = process_hero_image(asset_path, padding=0)

                        img_buffer = BytesIO()
                        img_processed.save(img_buffer, format='PNG', optimize=True)
                        img_bytes = img_buffer.getvalue()
                        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                        # Always store in cid_map -- still needed by /hero-image/ route
                        cid_map[cid] = img_base64

                        if url_mode:
                            # URL mode: replace with Jinja2 variable (no CID attachment)
                            html = html.replace(match, '{{ hero_image_url }}')
                            print(f"\u2705 Hero encoded for /hero-image/ route, src -> {{{{ hero_image_url }}}} ({len(img_bytes)} bytes)")
                        else:
                            html = html.replace(match, f"cid:{cid}")
                            print(f"\u2705 Successfully preprocessed and embedded {len(img_bytes)} bytes for {cid}")

                    elif is_interac and url_mode:
                        # URL mode: use {{ site_url }} Jinja variable -- resolved per deployment
                        jinja_url = "{{ site_url }}/static/images/email/interac-logo.jpg"
                        html = html.replace(match, jinja_url)
                        print(f"\u2705 Interac logo -> {{{{ site_url }}}} Jinja variable (not embedded)")
                        # Do NOT add to cid_map -- not needed by any route

                    else:
                        # Non-hero images (logos, etc.) -- no preprocessing
                        with open(asset_path, "rb") as img_file:
                            img_bytes = img_file.read()
                            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                            cid_map[cid] = img_base64

                        html = html.replace(match, f"cid:{cid}")
                        print(f"\u2705 Successfully embedded {len(img_bytes)} bytes for {cid}")

                except Exception as e:
                    print(f"\u274c ERROR: Failed to process image {asset_path}: {e}")
                    raise
            else:
                print(f"\u26a0\ufe0f  Image not found: {asset_path} (skipping)")

        # Always write to the compiled version (active version)
        print(f"\U0001f4be Writing HTML to: {target_html_path}")

        # Get timestamps before writing for verification
        target_html_exists_before = os.path.exists(target_html_path)
        target_html_mtime_before = os.path.getmtime(target_html_path) if target_html_exists_before else 0

        try:
            # Ensure we can write to the file by removing if it exists
            if os.path.exists(target_html_path):
                os.chmod(target_html_path, 0o666)  # Ensure writable

            with open(target_html_path, "w", encoding="utf-8") as f:
                f.write(html)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Ensure data is written to disk

            # Verify HTML file write
            if not os.path.exists(target_html_path):
                raise IOError(f"Failed to create target HTML file: {target_html_path}")

            target_html_size = os.path.getsize(target_html_path)
            target_html_mtime_after = os.path.getmtime(target_html_path)

            if target_html_size == 0:
                raise IOError(f"Target HTML file is empty: {target_html_path}")

            if target_html_mtime_after <= target_html_mtime_before:
                raise IOError(f"Target HTML file was not updated (timestamp unchanged): {target_html_path}")

            print(f"\u2705 Verified HTML written: {target_html_path} ({target_html_size} bytes, modified at {datetime.fromtimestamp(target_html_mtime_after)})")

        except Exception as e:
            print(f"\u274c ERROR: Failed to write HTML file {target_html_path}: {e}")
            raise

        # Write images JSON with verification
        print(f"\U0001f4be Writing images JSON to: {inline_images_path}")

        images_exists_before = os.path.exists(inline_images_path)
        images_mtime_before = os.path.getmtime(inline_images_path) if images_exists_before else 0

        try:
            # Ensure we can write to the file
            if os.path.exists(inline_images_path):
                os.chmod(inline_images_path, 0o666)  # Ensure writable

            with open(inline_images_path, "w", encoding="utf-8") as f:
                json.dump(cid_map, f, indent=2)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Ensure data is written to disk

            # Verify JSON file write
            if not os.path.exists(inline_images_path):
                raise IOError(f"Failed to create images JSON file: {inline_images_path}")

            images_size = os.path.getsize(inline_images_path)
            images_mtime_after = os.path.getmtime(inline_images_path)

            if images_size == 0:
                raise IOError(f"Images JSON file is empty: {inline_images_path}")

            if images_mtime_after <= images_mtime_before:
                raise IOError(f"Images JSON file was not updated (timestamp unchanged): {inline_images_path}")

            print(f"\u2705 Verified JSON written: {inline_images_path} ({images_size} bytes, modified at {datetime.fromtimestamp(images_mtime_after)})")

        except Exception as e:
            print(f"\u274c ERROR: Failed to write images JSON file {inline_images_path}: {e}")
            raise

        # UPDATED LOGIC: Write to original based on update_original flag
        if update_original:
            # Production deployment mode: ALWAYS update original (pristine defaults)
            print(f"\U0001f4be Updating original (pristine) files...")

            try:
                # Ensure we can write to the files
                if os.path.exists(original_html_path):
                    os.chmod(original_html_path, 0o666)
                if os.path.exists(original_images_path):
                    os.chmod(original_images_path, 0o666)

                with open(original_html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                    f.flush()
                    os.fsync(f.fileno())

                with open(original_images_path, "w", encoding="utf-8") as f:
                    json.dump(cid_map, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())

                print(f"\u2705 Updated original (pristine) files - customers will see this when resetting")
            except Exception as e:
                print(f"\u274c ERROR: Failed to update original files: {e}")
                raise
        elif not original_exists:
            # Development mode: Only create original if doesn't exist (first time)
            print(f"\U0001f4be Creating original backup files (first time)...")

            try:
                with open(original_html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                    f.flush()
                    os.fsync(f.fileno())

                with open(original_images_path, "w", encoding="utf-8") as f:
                    json.dump(cid_map, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())

                print(f"\u2705 Created original backup files")
            except Exception as e:
                print(f"\u274c ERROR: Failed to create original backup files: {e}")
                raise
        else:
            # Development mode: Original exists, skip updating
            print(f"\u2139\ufe0f  Skipping original update (use --update-original to deploy new pristine defaults)")

        # Final success message with timing
        elapsed_time = time.time() - start_time

        if update_original:
            print(f"\U0001f389 SUCCESS: Compiled '{template_name}' -> '{template_name}_compiled' AND updated '{template_name}_original' (pristine) with {len(cid_map)} embedded image(s) in {elapsed_time:.2f}s")
        elif not original_exists:
            print(f"\U0001f389 SUCCESS: Compiled '{template_name}' -> '{template_name}_compiled' and created '{template_name}_original' with {len(cid_map)} embedded image(s) in {elapsed_time:.2f}s")
        else:
            print(f"\U0001f389 SUCCESS: Compiled '{template_name}' -> '{template_name}_compiled' with {len(cid_map)} embedded image(s) in {elapsed_time:.2f}s (Original preserved)")

        return True

    except PermissionError as e:
        print(f"\u274c ERROR: Permission denied during compilation of '{template_name}': {e}")
        print(f"\U0001f4a1 Try: chmod 755 {template_name}* or run with different permissions")
        return False

    except FileNotFoundError as e:
        print(f"\u274c ERROR: File not found during compilation of '{template_name}': {e}")
        print(f"\U0001f4a1 Check that the template directory and index.html file exist")
        return False

    except IOError as e:
        print(f"\u274c ERROR: IO error during compilation of '{template_name}': {e}")
        print(f"\U0001f4a1 Check disk space and file permissions")
        return False

    except Exception as e:
        print(f"\u274c ERROR: Unexpected error during compilation of '{template_name}': {e}")
        print(f"\U0001f4a1 Full error details:")
        traceback.print_exc()
        return False


def main():
    """Main function with improved argument handling and error reporting"""
    if len(sys.argv) < 2:
        print("\u274c ERROR: Template name required")
        print("\U0001f4a1 Usage: python compileEmailTemplate.py <template_name> [--update-original] [--url-mode]")
        print("\U0001f4a1 Available templates: signup, newPass, paymentReceived, latePayment, redeemPass, survey_invitation, signup_payment_first")
        print("")
        print("\U0001f4cb Modes:")
        print("   Development (default):   Updates _compiled only, preserves _original")
        print("   Production:              python compileEmailTemplate.py <name> --update-original")
        print("                            Updates BOTH _compiled AND _original (pristine defaults)")
        print("")
        print("\U0001f5bc\ufe0f  Image modes:")
        print("   CID inline (default):    Images embedded as MIME attachments (classic)")
        print("   URL-based:               python compileEmailTemplate.py <name> --url-mode")
        print("                            Hero -> {{ hero_image_url }}, interac -> hosted URL")
        print("                            inline_images.json still written (for /hero-image/ route)")
        print("")
        print("\U0001f3af Use --update-original when:")
        print("   - Deploying improved templates to production")
        print("   - You want customers to see new design when they click Reset")
        print("   - Updating the pristine defaults for all activities")
        sys.exit(1)

    folder = sys.argv[1]
    update_original = '--update-original' in sys.argv or '--update-pristine' in sys.argv
    url_mode = '--url-mode' in sys.argv

    print(f"\U0001f680 Email Template Compiler v3.2 - Starting compilation...")
    print(f"\U0001f4c5 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\U0001f4c1 Template: {folder}")
    if url_mode:
        print(f"\U0001f310 Image mode: URL-based (Phase 3 hybrid hosted images)")
    if update_original:
        print(f"\u26a0\ufe0f  WARNING: Will update pristine original - customers will see this when resetting!")
    print("\u2500" * 60)

    success = compile_email_template_to_folder(folder, update_original=update_original, url_mode=url_mode)

    print("\u2500" * 60)
    if success:
        print(f"\U0001f3af COMPILATION COMPLETED SUCCESSFULLY for '{folder}'")
        if update_original:
            print(f"\u2705 Pristine original updated - deploy to production!")
        print("")
        print("\u26a0\ufe0f  IMPORTANT: Clear the hero image cache for changes to take effect!")
        print("   Option 1: Restart Flask server")
        print("   Option 2: POST to /admin/clear-template-cache (while logged in)")
        print("   Option 3: curl -X POST http://localhost:5000/admin/clear-template-cache -b 'session=...'")
        sys.exit(0)
    else:
        print(f"\U0001f4a5 COMPILATION FAILED for '{folder}'")
        sys.exit(1)


# Run with folder argument
if __name__ == "__main__":
    main()
