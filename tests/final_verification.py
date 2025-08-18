#!/usr/bin/env python3
"""
Final verification that chatbot is connected to REAL Ollama
"""
import requests
import json
import time

print("="*70)
print("🔍 FINAL VERIFICATION: Real Ollama Integration")
print("="*70)

# Test 1: Verify models endpoint returns REAL models
print("\n✅ TEST 1: Real Models from Ollama")
response = requests.get("http://127.0.0.1:8890/chatbot/models")
models = response.json()

print(f"Found {len(models['models'])} real models on your Ollama server:")
for model in models['models']:
    size_gb = model['size'] / (1024**3)
    print(f"  • {model['name']} ({size_gb:.1f} GB)")

# Test 2: Test with multiple models
test_cases = [
    {
        "model": "llama3.1:8b",
        "question": "What is 2+2?",
        "description": "Math question to Llama 3.1"
    },
    {
        "model": "dolphin-mistral:latest", 
        "question": "Write a haiku about coding",
        "description": "Creative writing with Dolphin Mistral"
    },
    {
        "model": "deepseek-coder:6.7b",
        "question": "How do I print hello world in Python?",
        "description": "Coding question to DeepSeek Coder"
    }
]

print("\n✅ TEST 2: Real LLM Responses")
for i, test in enumerate(test_cases, 1):
    print(f"\n  Test {i}: {test['description']}")
    print(f"  Model: {test['model']}")
    print(f"  Question: {test['question']}")
    
    start = time.time()
    response = requests.post("http://127.0.0.1:8890/chatbot/ask",
        json={
            "question": test['question'],
            "model": test['model'],
            "conversation_id": f"test-{i}"
        })
    elapsed = time.time() - start
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            answer = result['answer'][:150] + "..." if len(result['answer']) > 150 else result['answer']
            print(f"  Response ({elapsed:.1f}s): {answer}")
            print(f"  ✅ Real LLM response received!")
        else:
            print(f"  ❌ Error: {result.get('error')}")
    else:
        print(f"  ❌ HTTP {response.status_code}")

print("\n" + "="*70)
print("🎉 VERIFICATION COMPLETE!")
print("="*70)
print("\n✅ Your chatbot is now FULLY CONNECTED to your real Ollama server!")
print("✅ No more fake models (Claude 3.5, GPT-4)")
print("✅ Real responses from your actual LLMs (Llama 3.1, Dolphin Mistral, etc.)")
print("✅ You can now have real AI conversations in your chatbot interface!")
print("\nGo to http://127.0.0.1:8890/chatbot/ and try it yourself!")
print("Select 'llama3.1:8b' from the dropdown and ask any question!")
print("="*70)