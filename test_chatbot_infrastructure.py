#!/usr/bin/env python3
"""
Test script for chatbot infrastructure
Tests basic functionality without requiring the full Flask app
"""
import sys
import os
import asyncio

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import specific modules without importing Flask-dependent routes
from chatbot_v2.providers.ollama import create_ollama_provider
from chatbot_v2.ai_providers import provider_manager, AIRequest
from chatbot_v2.security import SQLSecurity
from chatbot_v2.config import OLLAMA_BASE_URL


async def test_ollama_provider():
    """Test Ollama provider functionality"""
    print("🔧 Testing Ollama Provider...")
    
    try:
        # Create Ollama provider
        provider = create_ollama_provider(OLLAMA_BASE_URL)
        
        # Check availability
        is_available = provider.check_availability()
        print(f"   Ollama available: {is_available}")
        
        if not is_available:
            print("   ⚠️  Ollama server not available. Make sure it's running.")
            return False
        
        # Get available models
        models = provider.get_available_models()
        print(f"   Available models: {models}")
        
        if not models:
            print("   ⚠️  No models available. Install a model first (e.g., 'ollama pull dolphin-mistral')")
            return False
        
        # Test generation with a simple prompt
        request = AIRequest(
            prompt="Generate a simple SELECT SQL query to get all users",
            model=models[0],
            temperature=0.1,
            max_tokens=100
        )
        
        print(f"   Testing generation with model: {models[0]}")
        response = await provider.generate(request)
        
        if response.error:
            print(f"   ❌ Generation failed: {response.error}")
            return False
        
        print(f"   ✅ Generation successful!")
        print(f"   Response: {response.content[:100]}...")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Response time: {response.response_time_ms}ms")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ollama test failed: {e}")
        return False


def test_sql_security():
    """Test SQL security validation"""
    print("🛡️  Testing SQL Security...")
    
    test_cases = [
        ("SELECT * FROM user", True, "Valid SELECT query"),
        ("DROP TABLE user", False, "Blocked DROP statement"),
        ("SELECT * FROM user; DELETE FROM user", False, "Multiple statements"),
        ("SELECT * FROM nonexistent_table", False, "Unauthorized table"),
        ("SELECT name, email FROM user WHERE id = 1", True, "Valid query with WHERE"),
        ("SELECT /*comment*/ * FROM user", False, "SQL comment injection"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for sql, should_pass, description in test_cases:
        result = SQLSecurity.validate_sql(sql)
        
        if result.is_safe == should_pass:
            print(f"   ✅ {description}")
            passed += 1
        else:
            print(f"   ❌ {description} - Expected: {should_pass}, Got: {result.is_safe}")
            if result.error_message:
                print(f"      Error: {result.error_message}")
    
    print(f"   Security tests passed: {passed}/{total}")
    return passed == total


def test_provider_manager():
    """Test AI provider manager"""
    print("🤖 Testing Provider Manager...")
    
    try:
        # Clear any existing providers
        provider_manager.providers.clear()
        
        # Create and register Ollama provider
        ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
        provider_manager.register_provider(ollama_provider, is_primary=True)
        
        # Check status
        status = provider_manager.get_all_status()
        print(f"   Registered providers: {list(status.keys())}")
        
        if 'ollama' not in status:
            print("   ❌ Ollama provider not registered")
            return False
        
        print(f"   ✅ Provider manager working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Provider manager test failed: {e}")
        return False


def test_config():
    """Test configuration settings"""
    print("⚙️  Testing Configuration...")
    
    try:
        from chatbot_v2.config import (
            OLLAMA_BASE_URL, CHATBOT_ENABLE_OLLAMA,
            MAX_RESULT_ROWS, ALLOWED_SQL_KEYWORDS
        )
        
        print(f"   Ollama URL: {OLLAMA_BASE_URL}")
        print(f"   Ollama enabled: {CHATBOT_ENABLE_OLLAMA}")
        print(f"   Max result rows: {MAX_RESULT_ROWS}")
        print(f"   Allowed SQL keywords: {len(ALLOWED_SQL_KEYWORDS)}")
        
        print("   ✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False


async def run_tests():
    """Run all infrastructure tests"""
    print("🚀 Starting Chatbot Infrastructure Tests")
    print("=" * 50)
    
    test_results = []
    
    # Test configuration
    test_results.append(test_config())
    
    # Test SQL security
    test_results.append(test_sql_security())
    
    # Test provider manager
    test_results.append(test_provider_manager())
    
    # Test Ollama provider (async)
    test_results.append(await test_ollama_provider())
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Infrastructure is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_tests())
    
    if success:
        print("\n✅ Phase 1 infrastructure is complete and working!")
        print("Next: Proceed to Phase 2 (Chat Interface Implementation)")
    else:
        print("\n❌ Phase 1 has issues that need to be resolved.")
        print("Check your Ollama server and try again.")
    
    sys.exit(0 if success else 1)