#!/usr/bin/env python3
"""
Validate that the app.py import issues are fixed
"""
import sys
import os

def validate_app_py():
    """Check app.py for import issues"""
    print("🔍 Validating app.py fixes...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check for old chatbot imports
    old_imports = [
        'from chatbot import chat_bp',
        'app.register_blueprint(chat_bp)'
    ]
    
    issues_found = []
    
    for old_import in old_imports:
        if old_import in content:
            issues_found.append(f"❌ Found old import: {old_import}")
    
    # Check for new chatbot_v2 import
    if 'from chatbot_v2 import chatbot_bp' in content:
        print("✅ New chatbot_v2 import found")
    else:
        issues_found.append("❌ Missing new chatbot_v2 import")
    
    if 'app.register_blueprint(chatbot_bp)' in content:
        print("✅ New chatbot_bp registration found")
    else:
        issues_found.append("❌ Missing new chatbot_bp registration")
    
    # Check for removed files
    removed_files = [
        'chatbot_old_prototype.py',
        'templates/chat_old_prototype.html'
    ]
    
    for file_path in removed_files:
        if os.path.exists(file_path):
            issues_found.append(f"❌ Old file still exists: {file_path}")
        else:
            print(f"✅ Old file removed: {file_path}")
    
    if issues_found:
        print("\n❌ Issues found:")
        for issue in issues_found:
            print(f"   {issue}")
        return False
    else:
        print("\n🎉 All fixes applied correctly!")
        print("\n✅ Your app should now work correctly.")
        print("💡 To test:")
        print("   1. Activate your Python environment with Flask")
        print("   2. Run: python app.py")
        print("   3. Visit: http://localhost:8890/chatbot/")
        return True

if __name__ == "__main__":
    success = validate_app_py()
    sys.exit(0 if success else 1)