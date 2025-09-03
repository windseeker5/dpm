#!/usr/bin/env python3
"""
Temporary script to extract the ticket image from inline_images.json
"""
import json
import base64
import os

def extract_ticket_image():
    # Read the JSON file
    json_path = '/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass_compiled/inline_images.json'
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Look for the ticket image
        if 'ticket' in data:
            ticket_data = data['ticket']
            
            # Create defaults directory
            defaults_dir = '/home/kdresdell/Documents/DEV/minipass_env/app/static/uploads/defaults'
            os.makedirs(defaults_dir, exist_ok=True)
            
            # Decode and save the ticket image as default_hero.png
            if ticket_data.startswith('data:image/'):
                # Remove the data URL prefix (e.g., "data:image/png;base64,")
                header, encoded = ticket_data.split(',', 1)
                image_data = base64.b64decode(encoded)
                
                output_path = os.path.join(defaults_dir, 'default_hero.png')
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                print(f"✓ Successfully extracted ticket image to: {output_path}")
                return True
            else:
                # If it's just base64 without data URL prefix
                try:
                    image_data = base64.b64decode(ticket_data)
                    output_path = os.path.join(defaults_dir, 'default_hero.png')
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"✓ Successfully extracted ticket image to: {output_path}")
                    return True
                except Exception as e:
                    print(f"Error decoding base64: {e}")
                    return False
        else:
            print("Keys available in JSON:", list(data.keys())[:10])  # Show first 10 keys
            return False
            
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return False

if __name__ == "__main__":
    extract_ticket_image()