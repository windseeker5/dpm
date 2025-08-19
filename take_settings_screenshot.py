#!/usr/bin/env python3
"""
Take screenshot of the settings page to see current state
"""

import subprocess
import time
import os

# Use a simple Python script with selenium-like approach using firefox headless
script = '''
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-dev-shm-usage']
  });
  const page = await browser.newPage();
  
  try {
    // Navigate to login
    await page.goto('http://127.0.0.1:8890/login');
    await page.waitForLoadState('networkidle');
    
    // Login
    await page.fill('input[name="email"]', 'kdresdell@gmail.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Go to settings
    await page.goto('http://127.0.0.1:8890/setup');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot
    await page.screenshot({ path: '/tmp/settings_page.png', fullPage: true });
    console.log('Screenshot saved: /tmp/settings_page.png');
    
    // Test clicking a submenu item
    const orgLink = await page.$('[data-tab="org"]');
    if (orgLink) {
      await orgLink.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: '/tmp/settings_after_org_click.png', fullPage: true });
      console.log('Screenshot after org click: /tmp/settings_after_org_click.png');
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
})();
'''

# Since we don't have puppeteer, let's use a different approach
# Let's create a curl-based test to grab the HTML and analyze it

print("Creating a simple curl-based screenshot alternative...")

# Get the HTML content and save it
try:
    result = subprocess.run([
        'bash', '-c', 
        '''
        # Login and get session cookie
        curl -s -c /tmp/cookies.txt -b /tmp/cookies.txt \\
             -X POST -d "email=kdresdell@gmail.com&password=admin123" \\
             "http://127.0.0.1:8890/login" > /dev/null
        
        # Get settings page HTML
        curl -s -b /tmp/cookies.txt "http://127.0.0.1:8890/setup" > /tmp/settings_page.html
        
        echo "Settings page HTML saved to: /tmp/settings_page.html"
        echo "File size: $(wc -c < /tmp/settings_page.html) bytes"
        
        # Extract key elements
        echo ""
        echo "=== SUBMENU STRUCTURE ==="
        grep -A 20 'id="settings-submenu"' /tmp/settings_page.html | head -30
        
        echo ""
        echo "=== JAVASCRIPT FUNCTIONS ==="
        grep -B 2 -A 5 "showSettingsTab\\|preventDefault\\|localStorage" /tmp/settings_page.html
        '''
    ], capture_output=True, text=True, timeout=30)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
        
except subprocess.TimeoutExpired:
    print("Command timed out")
except Exception as e:
    print(f"Error: {e}")

print("\nYou can also manually test by opening: http://127.0.0.1:8890/setup")
print("Login: kdresdell@gmail.com / admin123")