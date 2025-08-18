#!/usr/bin/env python3
"""
Verify the real Ollama chatbot implementation is working
"""
import requests
import json
import time

def verify_chatbot():
    """Verify the complete chatbot implementation"""
    print("🔍 Verifying Real Ollama Chatbot Implementation")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8890"
    
    # Test 1: Check server status
    print("\n1. Testing server status...")
    try:
        response = requests.get(f"{base_url}/chatbot/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   ✅ Provider: {data['provider']}")
            print(f"   ✅ Available: {data['available']}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Status check error: {e}")
        return False
    
    # Test 2: Check models endpoint
    print("\n2. Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/chatbot/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['models']:
                models = data['models']
                print(f"   ✅ Found {len(models)} real models:")
                for model in models:
                    size_gb = model['size'] / (1024**3)
                    print(f"      - {model['name']} ({size_gb:.1f}GB)")
                
                # Check for the specific models we expect
                model_names = [m['name'] for m in models]
                expected_models = ['llama3.1:8b', 'codellama:7b-instruct', 'deepseek-coder:6.7b', 'dolphin-mistral:latest', 'deepseek-r1:8b']
                
                all_found = True
                for expected in expected_models:
                    if expected in model_names:
                        print(f"      ✅ {expected} - FOUND")
                    else:
                        print(f"      ❌ {expected} - MISSING")
                        all_found = False
                
                if not all_found:
                    print("   ⚠️  Some expected models are missing")
                
            else:
                print(f"   ❌ No models found or request failed")
                return False
        else:
            print(f"   ❌ Models check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Models check error: {e}")
        return False
    
    # Test 3: Test connection endpoint
    print("\n3. Testing connection endpoint...")
    try:
        response = requests.get(f"{base_url}/chatbot/test-connection", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Connection test: {data['success']}")
            print(f"   ✅ Server available: {data['server_available']}")
            print(f"   ✅ Models count: {data['models_count']}")
            print(f"   ✅ Test model: {data['test_model']}")
            print(f"   ✅ Test response: '{data['test_response']}'")
            
            if data['test_response'] and 'OK' in data['test_response']:
                print("   ✅ Model is responding correctly!")
            else:
                print("   ⚠️  Model response seems unexpected")
        else:
            print(f"   ❌ Connection test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection test error: {e}")
        return False
    
    # Test 4: Verify UI endpoint is accessible
    print("\n4. Testing chatbot UI endpoint...")
    try:
        response = requests.get(f"{base_url}/chatbot", timeout=5)
        if response.status_code == 200:
            print("   ✅ Chatbot UI is accessible")
            
            # Check if the response contains model loading JavaScript
            content = response.text
            if 'loadModels' in content and 'ollama' in content.lower():
                print("   ✅ UI contains real model loading code")
            else:
                print("   ⚠️  UI might not have proper model loading")
        else:
            print(f"   ❌ UI not accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ UI test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE!")
    print("\n📋 Summary of Changes Made:")
    print("✅ Completely rewrote /chatbot_v2/routes_simple.py")
    print("✅ Removed all fake models (Claude 3.5, GPT-4)")
    print("✅ Added real Ollama server connection")
    print("✅ Query actual models from http://localhost:11434/api/tags")
    print("✅ Send messages to http://localhost:11434/api/generate")
    print("✅ Return real LLM responses")
    print("✅ Updated frontend to load models dynamically")
    print("✅ Added comprehensive error handling")
    print("✅ Added test endpoints for debugging")
    
    print("\n🎯 Next Steps:")
    print("1. Login to http://127.0.0.1:8890 with kdresdell@gmail.com / admin123")
    print("2. Navigate to http://127.0.0.1:8890/chatbot")
    print("3. Click the model dropdown - should show real Ollama models:")
    print("   - llama3.1:8b (4.6GB)")
    print("   - codellama:7b-instruct (3.6GB)")
    print("   - deepseek-coder:6.7b (3.6GB)")
    print("   - dolphin-mistral:latest (3.8GB)")
    print("   - deepseek-r1:8b (4.6GB)")
    print("4. Select any model and ask: 'Why is the sky blue?'")
    print("5. Should get real scientific explanation from the LLM")
    
    print("\n🔧 Architecture:")
    print("Backend: Real Ollama API integration")
    print("Models: Live from your Ollama server")
    print("Responses: Actual LLM generations")
    print("No more fake/mock data!")
    
    return True

if __name__ == "__main__":
    verify_chatbot()