#!/usr/bin/env python3
"""
Test the chatbot UI to verify real models are loaded
"""
import time
import subprocess
import sys
from playwright.sync_api import sync_playwright
import os

def test_chatbot_ui():
    """Test the chatbot interface with Playwright"""
    print("🧪 Testing Chatbot UI with Real Ollama Models")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1200, 'height': 800})
        page = context.new_page()
        
        try:
            # Navigate to login page
            print("1. Navigating to login page...")
            page.goto("http://127.0.0.1:8890/login")
            page.wait_for_load_state('networkidle')
            
            # Login
            print("2. Logging in...")
            page.fill('input[name="email"]', 'kdresdell@gmail.com')
            page.fill('input[name="password"]', 'admin123')
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            
            # Navigate to chatbot
            print("3. Navigating to chatbot...")
            page.goto("http://127.0.0.1:8890/chatbot")
            page.wait_for_load_state('networkidle')
            
            # Wait for models to load
            print("4. Waiting for models to load...")
            time.sleep(3)
            
            # Take screenshot of initial state
            print("5. Taking screenshot of chatbot with real models...")
            screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/real-ollama-chatbot-models.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"   Screenshot saved: {screenshot_path}")
            
            # Click model dropdown to show available models
            print("6. Opening model dropdown...")
            page.click("#modelSelect")
            time.sleep(1)
            
            # Take screenshot of dropdown
            dropdown_screenshot = "/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/real-ollama-chatbot-dropdown.png"
            page.screenshot(path=dropdown_screenshot, full_page=True)
            print(f"   Dropdown screenshot saved: {dropdown_screenshot}")
            
            # Get dropdown content
            model_options = page.query_selector_all('.model-option')
            models_found = []
            for option in model_options:
                text = option.inner_text().strip()
                if text and not text.startswith('Loading'):
                    models_found.append(text)
            
            print(f"7. Found {len(models_found)} models:")
            for model in models_found:
                print(f"   - {model}")
            
            # Test sending a message
            print("8. Testing message sending...")
            page.click('#messageInputLarge')
            page.fill('#messageInputLarge', 'Hello! Please respond with just "OK" to confirm you are working.')
            page.click('#sendBtnLarge')
            
            # Wait for response
            print("9. Waiting for AI response...")
            page.wait_for_selector('.message.assistant', timeout=30000)
            
            # Take final screenshot
            final_screenshot = "/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/real-ollama-chatbot-working.png"
            page.screenshot(path=final_screenshot, full_page=True)
            print(f"   Final screenshot saved: {final_screenshot}")
            
            # Get AI response
            response_element = page.query_selector('.message.assistant .message-content')
            if response_element:
                ai_response = response_element.inner_text()
                print(f"10. AI Response: '{ai_response}'")
            
            print("\n✅ Test completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            # Take error screenshot
            error_screenshot = "/home/kdresdell/Documents/DEV/minipass_env/app/.playwright-mcp/chatbot-error.png"
            try:
                page.screenshot(path=error_screenshot)
                print(f"   Error screenshot saved: {error_screenshot}")
            except:
                pass
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_chatbot_ui()