#!/usr/bin/env python3
"""
Script to search for ticket image in the JSON file
"""
import json
import os

def find_ticket_in_json():
    json_path = '/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass_compiled/inline_images.json'
    
    try:
        # Try to read the file line by line to find "ticket"
        with open(json_path, 'r') as f:
            content = f.read()
            
        # Check if "ticket" appears in the content
        if '"ticket"' in content:
            print("Found 'ticket' key in the JSON file")
            
            # Try to parse as JSON
            try:
                data = json.loads(content)
                keys = list(data.keys())
                print(f"Total keys found: {len(keys)}")
                print(f"First 20 keys: {keys[:20]}")
                
                if 'ticket' in data:
                    ticket_value = data['ticket']
                    print(f"Ticket value type: {type(ticket_value)}")
                    if isinstance(ticket_value, str):
                        print(f"Ticket value length: {len(ticket_value)}")
                        print(f"Ticket value starts with: {ticket_value[:100]}...")
                        return ticket_value
                else:
                    print("'ticket' key not found in parsed JSON")
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                
        else:
            print("'ticket' string not found in file")
            # Show a sample of the content
            print(f"File size: {len(content)} characters")
            print(f"First 500 characters: {content[:500]}")
            
    except Exception as e:
        print(f"Error: {e}")
        
    return None

if __name__ == "__main__":
    ticket_data = find_ticket_in_json()
    if ticket_data:
        print("Successfully found ticket data!")
    else:
        print("Could not find ticket data")