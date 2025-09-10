import os
import re
import json
import base64
import sys
import time
import traceback
from datetime import datetime


def compile_email_template_to_folder(template_name: str):
    """Compile email template with comprehensive logging and error handling"""
    try:
        print(f"📧 Starting compilation of '{template_name}'")
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

        # Write to original version only if it doesn't exist (preserve pristine state)
        if not original_exists:
            print(f"💾 Creating original backup files...")
            
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
        
        # Final success message with timing
        elapsed_time = time.time() - start_time
        
        if not original_exists:
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
        print("💡 Usage: python compileEmailTemplate.py <template_name>")
        print("💡 Available templates: signup, newPass, paymentReceived, latePayment, redeemPass, email_survey_invitation")
        sys.exit(1)
    
    folder = sys.argv[1]
    print(f"🚀 Email Template Compiler v2.0 - Starting compilation...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Template: {folder}")
    print("─" * 60)
    
    success = compile_email_template_to_folder(folder)
    
    print("─" * 60)
    if success:
        print(f"🎯 COMPILATION COMPLETED SUCCESSFULLY for '{folder}'")
        sys.exit(0)
    else:
        print(f"💥 COMPILATION FAILED for '{folder}'")
        sys.exit(1)


# 🟢 Run with folder argument or fallback to "test"
if __name__ == "__main__":
    main()