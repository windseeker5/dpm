#!/usr/bin/env python3
"""
Test script for Gemini AI provider
Run this to verify Gemini integration works correctly
"""
import os
import sys
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot_v2.providers.gemini import create_gemini_provider
from chatbot_v2.ai_providers import AIRequest


def test_gemini_provider():
    """Test Gemini provider functionality"""

    print("=" * 60)
    print("GEMINI PROVIDER TEST")
    print("=" * 60)

    # Check if API key is configured
    api_key = os.environ.get('GOOGLE_AI_API_KEY')
    if not api_key:
        print("❌ ERROR: GOOGLE_AI_API_KEY environment variable not set")
        print("\nTo fix:")
        print("1. Get API key from: https://ai.google.dev/aistudio")
        print("2. Add to .env file: GOOGLE_AI_API_KEY=your_key_here")
        print("3. Run: source venv/bin/activate")
        print("4. Re-run this test")
        return False

    print(f"✅ API key configured: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Create provider
    print("Creating Gemini provider...")
    provider = create_gemini_provider(api_key)
    print(f"✅ Provider created: {provider.name}")
    print()

    # Check availability
    print("Checking Gemini API availability...")
    is_available = provider.check_availability()

    if not is_available:
        print("❌ Gemini API is not available")
        print(f"   Last check: {provider.last_check}")
        return False

    print("✅ Gemini API is available")
    print()

    # Get available models
    print("Fetching available models...")
    models = provider.get_available_models()
    print(f"✅ Found {len(models)} models:")
    for model in models:
        print(f"   - {model}")
    print()

    # Test SQL generation
    print("Testing SQL generation...")
    print("Question: 'Show me all users'")

    ai_request = AIRequest(
        prompt="Show me all users",
        system_prompt="You are a SQL expert. Generate a SELECT query to show all users from the 'user' table.",
        model='gemini-2.5-flash',
        temperature=0.1,
        max_tokens=200
    )

    async def run_test():
        response = await provider.generate(ai_request)
        return response

    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(run_test())
    loop.close()

    if response.error:
        print(f"❌ Generation failed: {response.error}")
        return False

    print(f"✅ SQL generated successfully!")
    print(f"   Provider: {response.provider}")
    print(f"   Model: {response.model}")
    print(f"   Tokens: {response.tokens_used}")
    print(f"   Time: {response.response_time_ms}ms")
    print(f"   Cost: ${response.cost_cents / 100:.4f}")
    print()
    print(f"Generated SQL:")
    print(f"   {response.content}")
    print()

    # Test cost calculation
    print("Testing cost calculation...")
    cost = provider.calculate_cost(1000, 500, 'gemini-1.5-flash')
    print(f"✅ Cost for 1000 input + 500 output tokens: ${cost / 100:.4f}")
    print()

    print("=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start Flask server: flask run")
    print("2. Visit: http://localhost:5000/chatbot")
    print("3. Try asking questions about your data")
    print()

    return True


if __name__ == '__main__':
    success = test_gemini_provider()
    sys.exit(0 if success else 1)
