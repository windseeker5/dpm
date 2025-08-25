#!/usr/bin/env python3
"""
SSE Performance Fix Script

This script implements the missing /api/event-stream endpoint that is causing
performance issues across all Minipass pages.

The script provides multiple fix options:
1. Quick Fix: Add empty SSE endpoint to stop failures
2. Full Implementation: Add working SSE with real-time notifications
3. Disable Option: Comment out SSE JavaScript loading
"""

import sys
from pathlib import Path

def read_app_py():
    """Read the current app.py file"""
    app_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/app.py")
    
    if not app_file.exists():
        print("❌ app.py not found")
        return None, None
        
    try:
        with open(app_file, 'r') as f:
            content = f.read()
        return content, app_file
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return None, None

def find_imports_section(content):
    """Find where to add new imports"""
    lines = content.split('\n')
    
    # Find the last import line
    last_import_line = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            last_import_line = i
    
    return last_import_line

def find_routes_section(content):
    """Find where to add new routes"""
    lines = content.split('\n')
    
    # Look for a good place to add API routes (after existing @app.route definitions)
    api_routes_start = -1
    for i, line in enumerate(lines):
        if '@app.route' in line and '/api/' in line:
            api_routes_start = i
            break
    
    # If no API routes found, look for any route
    if api_routes_start == -1:
        for i, line in enumerate(lines):
            if '@app.route' in line:
                # Find the end of this route function
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('@app.route'):
                    j += 1
                api_routes_start = j - 1
                break
    
    return api_routes_start

def generate_quick_fix_code():
    """Generate quick fix code (empty SSE endpoint)"""
    return '''
# SSE Event Stream Endpoint (Quick Fix)
@app.route('/api/event-stream')
def event_stream():
    """
    Server-Sent Events endpoint for real-time notifications
    Quick fix version - returns empty stream to prevent connection failures
    """
    def generate():
        # Send a heartbeat every 30 seconds to keep connection alive
        import time
        while True:
            yield f"data: {{'type': 'heartbeat', 'timestamp': '{time.time()}'}}\n\n"
            time.sleep(30)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )
'''

def generate_full_implementation_code():
    """Generate full SSE implementation"""
    return '''
# Import for SSE implementation
import json
import time
from threading import Event
from queue import Queue, Empty
import uuid

# Global SSE clients management
sse_clients = {}
sse_message_queue = Queue()

class SSEClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.queue = Queue()
        self.connected = True
    
    def send_message(self, data):
        if self.connected:
            try:
                self.queue.put(data, timeout=1)
            except:
                self.connected = False

def broadcast_sse_message(message_type, data):
    """Broadcast message to all connected SSE clients"""
    message = {
        'type': message_type,
        'data': data,
        'timestamp': time.time(),
        'id': str(uuid.uuid4())
    }
    
    # Add to global queue for new connections
    try:
        sse_message_queue.put(message, timeout=1)
    except:
        pass
    
    # Send to all connected clients
    for client_id, client in list(sse_clients.items()):
        if client.connected:
            client.send_message(message)
        else:
            # Clean up disconnected clients
            del sse_clients[client_id]

# SSE Event Stream Endpoint (Full Implementation)
@app.route('/api/event-stream')
def event_stream():
    """
    Server-Sent Events endpoint for real-time notifications
    Full implementation with proper client management
    """
    client_id = str(uuid.uuid4())
    client = SSEClient(client_id)
    sse_clients[client_id] = client
    
    def generate():
        try:
            # Send initial connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"
            
            while client.connected:
                try:
                    # Get message from client queue with timeout
                    message = client.queue.get(timeout=30)
                    yield f"data: {json.dumps(message)}\n\n"
                except Empty:
                    # Send heartbeat if no messages
                    heartbeat = {
                        'type': 'heartbeat',
                        'timestamp': time.time()
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
                except:
                    break
                    
        finally:
            # Clean up on disconnect
            client.connected = False
            if client_id in sse_clients:
                del sse_clients[client_id]
    
    response = Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )
    
    return response

def send_payment_notification(signup_id, payment_data):
    """Send payment notification via SSE"""
    broadcast_sse_message('payment', {
        'id': f'payment_{signup_id}_{int(time.time())}',
        'signup_id': signup_id,
        'user_name': payment_data.get('user_name', 'Unknown'),
        'email': payment_data.get('email', ''),
        'activity': payment_data.get('activity', 'Unknown Activity'),
        'amount': payment_data.get('amount', 0),
        'avatar': payment_data.get('avatar', ''),
        'timestamp': time.time()
    })

def send_signup_notification(signup_id, signup_data):
    """Send signup notification via SSE"""
    broadcast_sse_message('signup', {
        'id': f'signup_{signup_id}_{int(time.time())}',
        'signup_id': signup_id,
        'user_name': signup_data.get('user_name', 'Unknown'),
        'email': signup_data.get('email', ''),
        'activity': signup_data.get('activity', 'Unknown Activity'),
        'passport_type': signup_data.get('passport_type', ''),
        'passport_type_price': signup_data.get('passport_type_price', 0),
        'avatar': signup_data.get('avatar', ''),
        'timestamp': time.time()
    })
'''

def check_for_response_import(content):
    """Check if Response is already imported from Flask"""
    return 'from flask import' in content and 'Response' in content

def add_response_import(content):
    """Add Response to Flask imports if not present"""
    if check_for_response_import(content):
        return content
    
    lines = content.split('\n')
    
    # Find the Flask import line
    for i, line in enumerate(lines):
        if line.strip().startswith('from flask import'):
            # Add Response to the import
            if 'Response' not in line:
                # Add Response to the end of the import
                import_end = line.rfind(')')
                if import_end != -1:
                    lines[i] = line[:import_end] + ', Response' + line[import_end:]
                else:
                    lines[i] = line + ', Response'
            break
    
    return '\n'.join(lines)

def apply_quick_fix():
    """Apply the quick fix (empty SSE endpoint)"""
    content, app_file = read_app_py()
    if not content:
        return False
    
    # Check if route already exists
    if '/api/event-stream' in content:
        print("⚠️  /api/event-stream route already exists in app.py")
        return False
    
    # Add Response import if needed
    content = add_response_import(content)
    
    # Find where to insert the route
    routes_section = find_routes_section(content)
    if routes_section == -1:
        print("❌ Could not find suitable location to add route")
        return False
    
    # Insert the quick fix code
    lines = content.split('\n')
    quick_fix_lines = generate_quick_fix_code().strip().split('\n')
    
    # Insert after the found route
    lines[routes_section+1:routes_section+1] = quick_fix_lines
    
    # Write back to file
    try:
        backup_file = app_file.with_suffix('.py.backup')
        app_file.rename(backup_file)
        print(f"✅ Backup created: {backup_file}")
        
        with open(app_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Quick fix applied to {app_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False

def apply_full_implementation():
    """Apply the full SSE implementation"""
    content, app_file = read_app_py()
    if not content:
        return False
    
    # Check if route already exists
    if '/api/event-stream' in content:
        print("⚠️  /api/event-stream route already exists in app.py")
        return False
    
    # Add Response import if needed
    content = add_response_import(content)
    
    # Find where to insert the route
    routes_section = find_routes_section(content)
    if routes_section == -1:
        print("❌ Could not find suitable location to add route")
        return False
    
    # Insert the full implementation code
    lines = content.split('\n')
    full_impl_lines = generate_full_implementation_code().strip().split('\n')
    
    # Insert after the found route
    lines[routes_section+1:routes_section+1] = full_impl_lines
    
    # Write back to file
    try:
        backup_file = app_file.with_suffix('.py.backup')
        app_file.rename(backup_file)
        print(f"✅ Backup created: {backup_file}")
        
        with open(app_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Full SSE implementation applied to {app_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False

def disable_sse_loading():
    """Disable SSE JavaScript loading in base template"""
    base_template = Path("/home/kdresdell/Documents/DEV/minipass_env/app/templates/base.html")
    
    if not base_template.exists():
        print("❌ base.html template not found")
        return False
    
    try:
        with open(base_template, 'r') as f:
            content = f.read()
        
        # Comment out the event-notifications.js loading
        original_line = '<script src="{{ url_for(\'static\', filename=\'js/event-notifications.js\') }}?v=1.0"></script>'
        commented_line = '<!-- SSE DISABLED: ' + original_line + ' -->'
        
        if original_line in content:
            content = content.replace(original_line, commented_line)
            
            # Create backup
            backup_file = base_template.with_suffix('.html.backup')
            base_template.rename(backup_file)
            print(f"✅ Backup created: {backup_file}")
            
            # Write updated content
            with open(base_template, 'w') as f:
                f.write(content)
            
            print(f"✅ SSE JavaScript loading disabled in {base_template}")
            return True
        else:
            print("⚠️  event-notifications.js script tag not found in expected format")
            return False
            
    except Exception as e:
        print(f"❌ Error disabling SSE loading: {e}")
        return False

def revert_changes():
    """Revert changes using backup files"""
    app_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/app.py")
    base_file = Path("/home/kdresdell/Documents/DEV/minipass_env/app/templates/base.html")
    
    app_backup = app_file.with_suffix('.py.backup')
    base_backup = base_file.with_suffix('.html.backup')
    
    reverted = []
    
    if app_backup.exists():
        try:
            app_backup.rename(app_file)
            reverted.append("app.py")
            print(f"✅ Reverted {app_file}")
        except Exception as e:
            print(f"❌ Error reverting app.py: {e}")
    
    if base_backup.exists():
        try:
            base_backup.rename(base_file)
            reverted.append("base.html")
            print(f"✅ Reverted {base_file}")
        except Exception as e:
            print(f"❌ Error reverting base.html: {e}")
    
    if reverted:
        print(f"✅ Successfully reverted: {', '.join(reverted)}")
    else:
        print("ℹ️  No backup files found to revert")

def main():
    """Main function with user interface"""
    print("🔧 MINIPASS SSE PERFORMANCE FIX TOOL")
    print("=" * 40)
    
    print("This tool fixes the Server-Sent Events (SSE) performance issue")
    print("causing 20+ failed requests on every page.\n")
    
    print("Choose an option:")
    print("1. ⚡ QUICK FIX - Add empty SSE endpoint (stops failures)")
    print("2. 🚀 FULL IMPLEMENTATION - Add working SSE with real-time notifications")
    print("3. 🚫 DISABLE SSE - Comment out SSE JavaScript loading")
    print("4. 🔄 REVERT CHANGES - Restore from backup files")
    print("5. ❌ EXIT - No changes")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print("\n⚡ Applying Quick Fix...")
            if apply_quick_fix():
                print("\n✅ QUICK FIX APPLIED SUCCESSFULLY!")
                print("The Flask server will auto-reload with the new route.")
                print("Test the pages to confirm the SSE failures are resolved.")
            break
            
        elif choice == '2':
            print("\n🚀 Applying Full Implementation...")
            if apply_full_implementation():
                print("\n✅ FULL SSE IMPLEMENTATION APPLIED SUCCESSFULLY!")
                print("The Flask server will auto-reload with the new functionality.")
                print("You can now send real-time notifications using:")
                print("  • broadcast_sse_message(type, data)")
                print("  • send_payment_notification(signup_id, payment_data)")
                print("  • send_signup_notification(signup_id, signup_data)")
            break
            
        elif choice == '3':
            print("\n🚫 Disabling SSE JavaScript...")
            if disable_sse_loading():
                print("\n✅ SSE JAVASCRIPT LOADING DISABLED!")
                print("Refresh browser pages to see the change.")
                print("No more SSE connection attempts will be made.")
            break
            
        elif choice == '4':
            print("\n🔄 Reverting changes...")
            revert_changes()
            break
            
        elif choice == '5':
            print("\n❌ No changes made. Exiting.")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()