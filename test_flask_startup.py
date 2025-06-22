#!/usr/bin/env python3
"""
Test Flask app startup with new chatbot module
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_flask_app():
    """Test if Flask app can start successfully"""
    print("🧪 Testing Flask App Startup...")
    
    try:
        # Import the Flask app
        print("   Importing Flask app...")
        from app import app
        
        print("   ✅ Flask app imported successfully")
        
        # Test app context
        with app.app_context():
            print("   ✅ App context created successfully")
            
            # Check if chatbot blueprint is registered
            blueprints = [bp.name for bp in app.blueprints.values()]
            print(f"   Registered blueprints: {blueprints}")
            
            if 'chatbot' in blueprints:
                print("   ✅ Chatbot blueprint registered successfully")
            else:
                print("   ❌ Chatbot blueprint not found")
                return False
            
            # Test route registration
            routes = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith('chatbot.'):
                    routes.append(f"{rule.methods} {rule.rule} -> {rule.endpoint}")
            
            if routes:
                print("   ✅ Chatbot routes registered:")
                for route in routes:
                    print(f"      {route}")
            else:
                print("   ❌ No chatbot routes found")
                return False
        
        print("\n🎉 Flask app startup test PASSED!")
        return True
        
    except Exception as e:
        print(f"   ❌ Flask app startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flask_app()
    
    if success:
        print("\n✅ Phase 2 Chat Interface is ready!")
        print("🚀 You can now start the Flask app to test the chatbot")
        print("📝 Access the chatbot at: http://localhost:8890/chatbot/")
    else:
        print("\n❌ Phase 2 has issues that need to be resolved.")
    
    sys.exit(0 if success else 1)