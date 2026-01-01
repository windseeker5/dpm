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


def process_hero_image(image_path: str, padding: int = 0, target_width: int = 152):
    """
    Process hero images by:
    1. Removing white background (RGB 255,255,255) and cropping to actual content
    2. Resizing to standard width (90px) while keeping aspect ratio
       (matches HTML width="90" so email clients display correctly)

    Args:
        image_path: Path to the image file
        padding: Pixels of padding to add around cropped image (default: 0)
        target_width: Target width in pixels (default: 90, matches HTML display width)

    Returns:
        PIL Image object with processed image
    """
    try:
        # Open image
        img = Image.open(image_path)

        # Convert to RGB if needed (in case it's RGBA or other mode)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to numpy array for easier processing
        import numpy as np
        img_array = np.array(img)

        # Define "white" as pixels where R, G, B are all > 240 (nearly white)
        # Lowered from 250 to 240 to catch off-white backgrounds from AI generators
        white_threshold = 240
        is_white = (img_array[:, :, 0] > white_threshold) & \
                   (img_array[:, :, 1] > white_threshold) & \
                   (img_array[:, :, 2] > white_threshold)

        # Find rows and columns that contain non-white pixels
        rows_with_content = np.where(~is_white.all(axis=1))[0]
        cols_with_content = np.where(~is_white.all(axis=0))[0]

        if len(rows_with_content) > 0 and len(cols_with_content) > 0:
            # Get bounding box of non-white content
            top = rows_with_content[0]
            bottom = rows_with_content[-1] + 1
            left = cols_with_content[0]
            right = cols_with_content[-1] + 1

            # Crop to content
            img_cropped = img.crop((left, top, right, bottom))

            print(f"   📐 Cropped from {img.size} to {img_cropped.size} (removed white background)")

            # Step 2: Resize to target width (200px), keeping aspect ratio
            # This matches HTML width="200" so email clients display correctly
            current_width, current_height = img_cropped.size
            if current_width != target_width:
                scale_factor = target_width / current_width
                new_height = int(current_height * scale_factor)
                img_resized = img_cropped.resize((target_width, new_height), Image.Resampling.LANCZOS)
                print(f"   📏 Resized from {img_cropped.size} to {img_resized.size} (target width: {target_width}px)")
            else:
                img_resized = img_cropped
                print(f"   📏 Already at target width: {target_width}px")

            # Step 3: Replace all near-white pixels with pure white (255,255,255)
            # This eliminates gray backgrounds from AI-generated images
            img_resized_array = np.array(img_resized)
            near_white_mask = (img_resized_array[:, :, 0] > white_threshold) & \
                              (img_resized_array[:, :, 1] > white_threshold) & \
                              (img_resized_array[:, :, 2] > white_threshold)
            img_resized_array[near_white_mask] = [255, 255, 255]
            img_resized = Image.fromarray(img_resized_array)
            print(f"   🎨 Replaced near-white pixels with pure white (255,255,255)")

            if padding > 0:
                # Add padding if requested
                padded_width = img_resized.width + (padding * 2)
                padded_height = img_resized.height + (padding * 2)

                # Create new image with padding (white background)
                img_padded = Image.new('RGB', (padded_width, padded_height), (255, 255, 255))
                img_padded.paste(img_resized, (padding, padding))

                print(f"   ➕ Added {padding}px padding → final size: {img_padded.size}")
                return img_padded
            else:
                return img_resized
        else:
            # If no non-white content found, still resize to target width
            print(f"   ⚠️  No non-white content found, resizing original")
            current_width, current_height = img.size
            if current_width != target_width:
                scale_factor = target_width / current_width
                new_height = int(current_height * scale_factor)
                img_resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                print(f"   📏 Resized from {img.size} to {img_resized.size} (target width: {target_width}px)")
            else:
                img_resized = img

            # Replace near-white pixels with pure white
            img_resized_array = np.array(img_resized)
            near_white_mask = (img_resized_array[:, :, 0] > white_threshold) & \
                              (img_resized_array[:, :, 1] > white_threshold) & \
                              (img_resized_array[:, :, 2] > white_threshold)
            img_resized_array[near_white_mask] = [255, 255, 255]
            img_resized = Image.fromarray(img_resized_array)
            print(f"   🎨 Replaced near-white pixels with pure white (255,255,255)")
            return img_resized

    except Exception as e:
        print(f"⚠️  Warning: Could not process image {image_path}: {e}")
        print(f"⚠️  Returning original image without preprocessing")
        import traceback
        traceback.print_exc()
        # Return original image if processing fails
        return Image.open(image_path)


def compile_email_template_to_folder(template_name: str, update_original: bool = False):
    """
    Compile email template with comprehensive logging and error handling

    Args:
        template_name: Name of the template to compile (e.g., 'newPass', 'signup')
        update_original: If True, updates the pristine original folder (for production deployment)
                        If False, only updates compiled folder (for development/testing)
    """
    try:
        print(f"📧 Starting compilation of '{template_name}'")
        if update_original:
            print(f"🔄 MODE: Production Deployment (updating pristine original)")
        else:
            print(f"🛠️  MODE: Development (compiled only, original preserved)")

        start_time = time.time()

        source_dir = os.path.abspath(template_name)
        target_dir = os.path.abspath(f"{template_name}_compiled")
        original_dir = os.path.abspath(f"{template_name}_original")
        
        print(f"📂 Source path: {source_dir}")
        print(f"📂 Target path: {target_dir}")
        print(f"📂 Original path: {original_dir}")
        
        # Verify source directory exists
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Source directory '{source_dir}' does not exist")
        
        # Create both compiled and original directories
        os.makedirs(target_dir, exist_ok=True)
        print(f"✅ Created/verified target directory: {target_dir}")
        
        # Check if original version already exists (to preserve pristine version)
        original_exists = os.path.exists(original_dir)
        if not original_exists:
            os.makedirs(original_dir, exist_ok=True)
            print(f"✅ Created original directory: {original_dir}")
        else:
            print(f"ℹ️  Original directory already exists: {original_dir}")

        source_html_path = os.path.join(source_dir, "index.html")
        target_html_path = os.path.join(target_dir, "index.html")
        inline_images_path = os.path.join(target_dir, "inline_images.json")
        
        # Original paths (only created if doesn't exist)
        original_html_path = os.path.join(original_dir, "index.html")
        original_images_path = os.path.join(original_dir, "inline_images.json")
        
        # Verify source HTML file exists
        if not os.path.exists(source_html_path):
            raise FileNotFoundError(f"Source HTML file '{source_html_path}' does not exist")
        
        print(f"📄 Reading source HTML: {source_html_path}")
        with open(source_html_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        source_size = len(html)
        print(f"📏 Source HTML size: {source_size} characters")
        
        if source_size == 0:
            raise ValueError(f"Source HTML file '{source_html_path}' is empty")

        cid_map = {}
        
        # Match <img src="..."> tags
        matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        print(f"🖼️  Processing {len(matches)} images")
        
        for match in matches:
            asset_path = os.path.join(source_dir, os.path.basename(match))

            if os.path.exists(asset_path):
                cid = os.path.splitext(os.path.basename(asset_path))[0]
                print(f"📎 Embedding image: {asset_path} as cid:{cid}")

                try:
                    # Check if this is a hero image (should be preprocessed)
                    is_hero_image = any(hero_name in os.path.basename(asset_path).lower()
                                      for hero_name in ['hero', 'good-news', 'currency-dollar',
                                                       'hand-rock', 'thumb-down', 'sondage'])

                    if is_hero_image:
                        print(f"🎨 Preprocessing hero image (auto-crop, NO padding)...")
                        # Process the hero image (crop only, NO padding)
                        img_processed = process_hero_image(asset_path, padding=0)

                        # Convert to bytes
                        img_buffer = BytesIO()
                        img_processed.save(img_buffer, format='PNG', optimize=True)
                        img_bytes = img_buffer.getvalue()
                        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                        cid_map[cid] = img_base64

                        print(f"✅ Successfully preprocessed and embedded {len(img_bytes)} bytes for {cid}")
                    else:
                        # Non-hero images (QR codes, logos, etc.) - no preprocessing
                        with open(asset_path, "rb") as img_file:
                            img_bytes = img_file.read()
                            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                            cid_map[cid] = img_base64

                        print(f"✅ Successfully embedded {len(img_bytes)} bytes for {cid}")

                    # Replace img src with cid:...
                    html = html.replace(match, f"cid:{cid}")
                except Exception as e:
                    print(f"❌ ERROR: Failed to process image {asset_path}: {e}")
                    raise
            else:
                print(f"⚠️  Image not found: {asset_path} (skipping)")

        # Always write to the compiled version (active version)
        print(f"💾 Writing HTML to: {target_html_path}")
        
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
            
            print(f"✅ Verified HTML written: {target_html_path} ({target_html_size} bytes, modified at {datetime.fromtimestamp(target_html_mtime_after)})")
        
        except Exception as e:
            print(f"❌ ERROR: Failed to write HTML file {target_html_path}: {e}")
            raise
        
        # Write images JSON with verification
        print(f"💾 Writing images JSON to: {inline_images_path}")
        
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
            
            print(f"✅ Verified JSON written: {inline_images_path} ({images_size} bytes, modified at {datetime.fromtimestamp(images_mtime_after)})")
        
        except Exception as e:
            print(f"❌ ERROR: Failed to write images JSON file {inline_images_path}: {e}")
            raise

        # UPDATED LOGIC: Write to original based on update_original flag
        if update_original:
            # Production deployment mode: ALWAYS update original (pristine defaults)
            print(f"💾 Updating original (pristine) files...")

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

                print(f"✅ Updated original (pristine) files - customers will see this when resetting")
            except Exception as e:
                print(f"❌ ERROR: Failed to update original files: {e}")
                raise
        elif not original_exists:
            # Development mode: Only create original if doesn't exist (first time)
            print(f"💾 Creating original backup files (first time)...")

            try:
                with open(original_html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                    f.flush()
                    os.fsync(f.fileno())

                with open(original_images_path, "w", encoding="utf-8") as f:
                    json.dump(cid_map, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())

                print(f"✅ Created original backup files")
            except Exception as e:
                print(f"❌ ERROR: Failed to create original backup files: {e}")
                raise
        else:
            # Development mode: Original exists, skip updating
            print(f"ℹ️  Skipping original update (use --update-original to deploy new pristine defaults)")

        # Final success message with timing
        elapsed_time = time.time() - start_time

        if update_original:
            print(f"🎉 SUCCESS: Compiled '{template_name}' → '{template_name}_compiled' AND updated '{template_name}_original' (pristine) with {len(cid_map)} embedded image(s) in {elapsed_time:.2f}s")
        elif not original_exists:
            print(f"🎉 SUCCESS: Compiled '{template_name}' → '{template_name}_compiled' and created '{template_name}_original' with {len(cid_map)} embedded image(s) in {elapsed_time:.2f}s")
        else:
            print(f"🎉 SUCCESS: Compiled '{template_name}' → '{template_name}_compiled' with {len(cid_map)} embedded image(s) in {elapsed_time:.2f}s (Original preserved)")
        
        return True
    
    except PermissionError as e:
        print(f"❌ ERROR: Permission denied during compilation of '{template_name}': {e}")
        print(f"💡 Try: chmod 755 {template_name}* or run with different permissions")
        return False
    
    except FileNotFoundError as e:
        print(f"❌ ERROR: File not found during compilation of '{template_name}': {e}")
        print(f"💡 Check that the template directory and index.html file exist")
        return False
    
    except IOError as e:
        print(f"❌ ERROR: IO error during compilation of '{template_name}': {e}")
        print(f"💡 Check disk space and file permissions")
        return False
    
    except Exception as e:
        print(f"❌ ERROR: Unexpected error during compilation of '{template_name}': {e}")
        print(f"💡 Full error details:")
        traceback.print_exc()
        return False


def main():
    """Main function with improved argument handling and error reporting"""
    if len(sys.argv) < 2:
        print("❌ ERROR: Template name required")
        print("💡 Usage: python compileEmailTemplate.py <template_name> [--update-original]")
        print("💡 Available templates: signup, newPass, paymentReceived, latePayment, redeemPass, survey_invitation")
        print("")
        print("📋 Modes:")
        print("   Development (default):   Updates _compiled only, preserves _original")
        print("   Production:              python compileEmailTemplate.py <name> --update-original")
        print("                            Updates BOTH _compiled AND _original (pristine defaults)")
        print("")
        print("🎯 Use --update-original when:")
        print("   - Deploying improved templates to production")
        print("   - You want customers to see new design when they click Reset")
        print("   - Updating the pristine defaults for all activities")
        sys.exit(1)

    folder = sys.argv[1]
    update_original = '--update-original' in sys.argv or '--update-pristine' in sys.argv

    print(f"🚀 Email Template Compiler v3.0 - Starting compilation...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Template: {folder}")
    if update_original:
        print(f"⚠️  WARNING: Will update pristine original - customers will see this when resetting!")
    print("─" * 60)

    success = compile_email_template_to_folder(folder, update_original=update_original)

    print("─" * 60)
    if success:
        print(f"🎯 COMPILATION COMPLETED SUCCESSFULLY for '{folder}'")
        if update_original:
            print(f"✅ Pristine original updated - deploy to production!")
        print("")
        print("⚠️  IMPORTANT: Clear the hero image cache for changes to take effect!")
        print("   Option 1: Restart Flask server")
        print("   Option 2: POST to /admin/clear-template-cache (while logged in)")
        print("   Option 3: curl -X POST http://localhost:5000/admin/clear-template-cache -b 'session=...'")
        sys.exit(0)
    else:
        print(f"💥 COMPILATION FAILED for '{folder}'")
        sys.exit(1)


# 🟢 Run with folder argument or fallback to "test"
if __name__ == "__main__":
    main()