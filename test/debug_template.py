#!/usr/bin/env python3
"""
Debug template rendering
"""
import sys
import os

# Add the parent directory to sys.path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Setting

def debug_template():
    """Debug template content"""
    with app.test_client() as client:
        with app.app_context():
            # Create a test session
            with client.session_transaction() as sess:
                sess['admin'] = 'test@example.com'
            
            # Test GET request
            response = client.get('/admin/unified-settings')
            content = response.data.decode('utf-8')
            
            print("=== CHECKING FORM ACTION ===")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'form' in line and 'action' in line:
                    print(f"Line {i}: {line.strip()}")
            
            print("\n=== CHECKING URL_FOR RESOLUTION ===")
            # Check if save_unified_settings is found in form
            form_lines = [line for line in lines if 'save_unified_settings' in line]
            for line in form_lines:
                print(f"Found: {line.strip()}")
                
            print("\n=== CHECKING SETTINGS VALUES ===")
            # Look for ORG_NAME field
            org_lines = [line for line in lines if 'ORG_NAME' in line]
            for line in org_lines:
                print(f"Found: {line.strip()}")

if __name__ == '__main__':
    debug_template()