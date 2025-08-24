#!/usr/bin/env python3
"""
Playwright test for notification HTML endpoints
"""

async def test_notification_endpoints():
    """Test notification endpoints with proper session"""
    
    from playwright.async_api import async_playwright
    import json
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # Login first
            await page.goto("http://127.0.0.1:8890/login")
            await page.fill("input[name='email']", "kdresdell@gmail.com")
            await page.fill("input[name='password']", "admin123")
            await page.click("button[type='submit']")
            
            # Wait for redirect after successful login
            await page.wait_for_url("http://127.0.0.1:8890/dashboard")
            print("✅ Successfully logged in as admin")
            
            # Test payment notification endpoint
            payment_data = {
                "type": "payment",
                "id": "payment_123_1640995200",
                "timestamp": "2024-01-24T10:00:00Z",
                "data": {
                    "user_name": "John Doe",
                    "email": "john@example.com",
                    "avatar": "https://www.gravatar.com/avatar/placeholder",
                    "amount": 175.00,
                    "activity": "Mountain Biking",
                    "activity_id": 1,
                    "paid_date": "2024-01-24T10:00:00Z"
                }
            }
            
            # Make API call using page.evaluate to access session
            payment_response = await page.evaluate(f"""
                fetch('/api/payment-notification-html/test123', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({json.dumps(payment_data)})
                }}).then(response => {{
                    return {{
                        status: response.status,
                        ok: response.ok,
                        text: response.text()
                    }};
                }}).then(async (result) => {{
                    return {{
                        ...result,
                        text: await result.text
                    }};
                }});
            """)
            
            print(f"\nPayment notification endpoint:")
            print(f"Status: {payment_response['status']}")
            print(f"OK: {payment_response['ok']}")
            
            if payment_response['ok']:
                html_content = payment_response['text']
                print("✅ Payment notification endpoint working!")
                print(f"HTML length: {len(html_content)}")
                print(f"Contains notification: {'event-notification' in html_content}")
                print(f"Contains payment icon: {'ti-credit-card' in html_content}")
                print(f"Contains user name: {'John Doe' in html_content}")
            else:
                print(f"❌ Payment notification endpoint failed: {payment_response['text']}")
            
            # Test signup notification endpoint
            signup_data = {
                "type": "signup", 
                "id": "signup_456_1640995300",
                "timestamp": "2024-01-24T10:05:00Z",
                "data": {
                    "user_name": "Jane Smith",
                    "email": "jane@example.com",
                    "avatar": "https://www.gravatar.com/avatar/placeholder2", 
                    "activity": "Rock Climbing",
                    "activity_id": 2,
                    "passport_type": "Standard Pass",
                    "passport_type_price": 50.00,
                    "phone": "+1234567890"
                }
            }
            
            signup_response = await page.evaluate(f"""
                fetch('/api/signup-notification-html/test456', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({json.dumps(signup_data)})
                }}).then(response => {{
                    return {{
                        status: response.status,
                        ok: response.ok,
                        text: response.text()
                    }};
                }}).then(async (result) => {{
                    return {{
                        ...result,
                        text: await result.text
                    }};
                }});
            """)
            
            print(f"\nSignup notification endpoint:")
            print(f"Status: {signup_response['status']}")
            print(f"OK: {signup_response['ok']}")
            
            if signup_response['ok']:
                html_content = signup_response['text']
                print("✅ Signup notification endpoint working!")
                print(f"HTML length: {len(html_content)}")
                print(f"Contains notification: {'event-notification' in html_content}")
                print(f"Contains signup icon: {'ti-user-plus' in html_content}")
                print(f"Contains user name: {'Jane Smith' in html_content}")
            else:
                print(f"❌ Signup notification endpoint failed: {signup_response['text']}")
                
        except Exception as e:
            print(f"Error during testing: {str(e)}")
        
        finally:
            await browser.close()

# Run the test
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_notification_endpoints())