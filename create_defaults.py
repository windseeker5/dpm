#!/usr/bin/env python3
"""
Create default images for email templates
"""
import json
import base64
import os
import shutil

def create_defaults():
    # Create defaults directory
    defaults_dir = '/home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/defaults'
    os.makedirs(defaults_dir, exist_ok=True)
    print(f"✓ Created defaults directory: {defaults_dir}")
    
    # Step 1: Copy logo.png as default_owner_logo.png
    logo_source = '/home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/logo.png'
    logo_dest = os.path.join(defaults_dir, 'default_owner_logo.png')
    
    try:
        shutil.copy2(logo_source, logo_dest)
        print(f"✓ Successfully copied logo to: {logo_dest}")
    except Exception as e:
        print(f"✗ Error copying logo: {e}")
        return False
    
    # Step 2: Extract ticket image from JSON
    json_path = '/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass_compiled/inline_images.json'
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        print(f"✓ Successfully loaded JSON with {len(data)} keys")
        
        # Look for ticket image
        if 'ticket' in data:
            ticket_data = data['ticket']
            print(f"✓ Found ticket image data (length: {len(ticket_data)})")
            
            # Decode and save the ticket image
            try:
                if ticket_data.startswith('data:image/'):
                    # Remove data URL prefix
                    header, encoded = ticket_data.split(',', 1)
                    image_data = base64.b64decode(encoded)
                else:
                    # Direct base64
                    image_data = base64.b64decode(ticket_data)
                
                hero_dest = os.path.join(defaults_dir, 'default_hero.png')
                with open(hero_dest, 'wb') as f:
                    f.write(image_data)
                
                print(f"✓ Successfully extracted ticket image to: {hero_dest}")
                return True
                
            except Exception as e:
                print(f"✗ Error decoding ticket image: {e}")
                return False
        else:
            # Show available keys to debug
            keys = list(data.keys())
            print(f"✗ 'ticket' key not found. Available keys (first 20): {keys[:20]}")
            
            # Look for similar keys
            ticket_like = [k for k in keys if 'ticket' in k.lower()]
            if ticket_like:
                print(f"Found ticket-like keys: {ticket_like}")
            
            return False
            
    except Exception as e:
        print(f"✗ Error processing JSON file: {e}")
        return False

if __name__ == "__main__":
    success = create_defaults()
    if success:
        print("\n🎉 All default images created successfully!")
    else:
        print("\n❌ Some operations failed. Check the output above.")

# Execute the function
create_defaults()