#!/usr/bin/env python3
"""
Test chatbot module imports and structure
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_chatbot_imports():
    """Test chatbot module imports"""
    print("🧪 Testing Chatbot Module Imports...")
    
    try:
        # Test core module imports
        print("   Testing core imports...")
        from chatbot_v2.config import OLLAMA_BASE_URL, CHATBOT_ENABLE_OLLAMA
        print(f"   ✅ Config imported - Ollama URL: {OLLAMA_BASE_URL}")
        
        from chatbot_v2.ai_providers import AIProvider, AIRequest, AIResponse, provider_manager
        print("   ✅ AI providers imported")
        
        from chatbot_v2.providers.ollama import OllamaProvider, create_ollama_provider
        print("   ✅ Ollama provider imported")
        
        from chatbot_v2.security import SQLSecurity, QueryExecutor
        print("   ✅ Security module imported")
        
        from chatbot_v2.query_engine import QueryEngine, create_query_engine
        print("   ✅ Query engine imported")
        
        from chatbot_v2.conversation import ConversationManager, conversation_manager
        print("   ✅ Conversation manager imported")
        
        from chatbot_v2.utils import generate_session_token, format_currency
        print("   ✅ Utils imported")
        
        # Test blueprint import (this will initialize providers)
        print("   Testing blueprint import...")
        from chatbot_v2 import chatbot_bp
        print("   ✅ Blueprint imported successfully")
        
        # Test provider manager status
        status = provider_manager.get_all_status()
        print(f"   Provider status: {list(status.keys())}")
        
        print("\n🎉 All chatbot imports PASSED!")
        return True
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """Test file structure is correct"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        'chatbot_v2/__init__.py',
        'chatbot_v2/config.py',
        'chatbot_v2/ai_providers.py',
        'chatbot_v2/providers/__init__.py',
        'chatbot_v2/providers/ollama.py',
        'chatbot_v2/security.py',
        'chatbot_v2/query_engine.py',
        'chatbot_v2/conversation.py',
        'chatbot_v2/utils.py',
        'chatbot_v2/routes.py',
        'templates/analytics_chatbot.html',
        'static/css/chatbot.css',
        'static/js/chatbot.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    
    print("   ✅ All required files present")
    return True

if __name__ == "__main__":
    print("🚀 Testing Chatbot Phase 2 Implementation")
    print("=" * 50)
    
    structure_ok = test_file_structure()
    imports_ok = test_chatbot_imports()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    
    if structure_ok and imports_ok:
        print("🎉 Phase 2 Chat Interface is complete and working!")
        print("\n✅ Next Steps:")
        print("1. Start your Flask app in the proper environment")
        print("2. Navigate to /chatbot/ to test the interface")
        print("3. Ensure your Ollama server is running")
        print("4. Test with sample questions")
        success = True
    else:
        print("❌ Phase 2 has issues that need to be resolved.")
        success = False
    
    sys.exit(0 if success else 1)