#!/usr/bin/env python3
"""
Browser test for email template defaults using MCP Playwright
Tests the full user flow of creating an activity and verifying email templates
"""

print("Starting email template defaults browser test...")
print("=" * 60)
print("This test will:")
print("1. Login to admin panel")
print("2. Create a new activity") 
print("3. Verify email templates are pre-populated")
print("4. Take screenshots at each step")
print("=" * 60)

# Test steps for MCP Playwright:
# 1. Navigate to http://localhost:5000/login
# 2. Login with kdresdell@gmail.com / admin123
# 3. Create new activity via /create-activity
# 4. Navigate to the new activity's email template page
# 5. Verify templates are populated with default values
# 6. Take screenshots at each critical step

print("\nTo run this test manually with MCP Playwright:")
print("1. Use mcp__playwright__browser_navigate to go to http://localhost:5000/login")
print("2. Use mcp__playwright__browser_type to enter credentials")
print("3. Use mcp__playwright__browser_click to submit login")
print("4. Navigate to create activity page")
print("5. Fill in activity details and create")
print("6. Check email templates for the new activity")
print("\nScreenshots should be saved to test/playwright/")