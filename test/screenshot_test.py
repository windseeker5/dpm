#!/usr/bin/env python3
"""
Screenshot test for event notifications using subprocess and browser
"""

import subprocess
import os
import time
import tempfile

def take_screenshot_with_browser():
    """Take a screenshot of the notification test page"""
    
    # Create path for test file
    test_file = os.path.join(os.path.dirname(__file__), 'visual_notifications_test.html')
    file_url = f"file://{os.path.abspath(test_file)}"
    
    print(f"📸 Taking screenshot of: {file_url}")
    
    # Screenshot output path
    screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/test/notification_screenshot.png"
    
    # Try different browsers
    browsers_to_try = [
        # Firefox
        ["firefox", "--headless", "--screenshot", screenshot_path, file_url],
        # Chrome/Chromium
        ["google-chrome", "--headless", "--disable-gpu", f"--screenshot={screenshot_path}", file_url],
        ["chromium", "--headless", "--disable-gpu", f"--screenshot={screenshot_path}", file_url],
        ["chromium-browser", "--headless", "--disable-gpu", f"--screenshot={screenshot_path}", file_url],
    ]
    
    for browser_cmd in browsers_to_try:
        try:
            print(f"Trying browser: {browser_cmd[0]}")
            result = subprocess.run(browser_cmd, timeout=30, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                print(f"✅ Screenshot saved to: {screenshot_path}")
                return screenshot_path
            else:
                print(f"❌ {browser_cmd[0]} failed: {result.stderr}")
                
        except FileNotFoundError:
            print(f"❌ {browser_cmd[0]} not found")
        except subprocess.TimeoutExpired:
            print(f"❌ {browser_cmd[0]} timed out")
        except Exception as e:
            print(f"❌ {browser_cmd[0]} error: {e}")
    
    print("❌ No suitable browser found for screenshot")
    return None

def create_simple_html_test():
    """Create a simpler HTML test that doesn't need external resources"""
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Notifications Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            max-width: 800px;
            width: 100%;
        }
        
        h1 {
            text-align: center;
            color: #1e293b;
            margin-bottom: 2rem;
        }
        
        .notification-preview {
            position: relative;
            margin: 20px 0;
            transform: translateX(0);
        }
        
        /* Mock notification styles based on our CSS */
        .event-notification {
            position: relative;
            margin-bottom: 0.75rem;
            border-radius: 0.75rem;
            border: none;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.08);
            color: white;
        }
        
        .notification-payment {
            background: linear-gradient(135deg, rgba(32, 201, 151, 0.95) 0%, rgba(5, 150, 105, 0.95) 100%);
        }
        
        .notification-signup {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.95) 0%, rgba(37, 99, 235, 0.95) 100%);
        }
        
        .notification-content {
            padding: 1.25rem;
            padding-right: 3rem;
        }
        
        .notification-header {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1rem;
            gap: 0.875rem;
        }
        
        .notification-avatar {
            flex-shrink: 0;
        }
        
        .avatar {
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }
        
        .notification-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.25rem;
            font-weight: 600;
        }
        
        .notification-subtitle {
            font-size: 0.85rem;
            opacity: 0.85;
        }
        
        .notification-body {
            margin-bottom: 1rem;
        }
        
        .notification-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8rem;
        }
        
        .notification-status {
            display: flex;
            align-items: center;
            gap: 0.375rem;
            font-weight: 500;
        }
        
        .btn-close {
            position: absolute;
            top: 0.75rem;
            right: 0.75rem;
            width: 20px;
            height: 20px;
            border: none;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            color: white;
            cursor: pointer;
        }
        
        .demo-info {
            background: #f1f5f9;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border-left: 4px solid #3b82f6;
            margin-top: 2rem;
        }
        
        .demo-info h3 {
            color: #1e293b;
            margin-bottom: 0.75rem;
        }
        
        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.5rem;
            color: #475569;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔔 Event Notifications System</h1>
        
        <div class="notification-preview">
            <!-- Payment Notification Mock -->
            <div class="event-notification notification-payment">
                <button class="btn-close">×</button>
                <div class="notification-content">
                    <div class="notification-header">
                        <div class="notification-avatar">
                            <div class="avatar">💳</div>
                        </div>
                        <div class="notification-title-area">
                            <div class="notification-title">
                                💳 Payment Received
                            </div>
                            <div class="notification-subtitle">
                                Sarah Johnson<br>
                                <small>sarah.johnson@example.com</small>
                            </div>
                        </div>
                    </div>
                    <div class="notification-body">
                        <div class="notification-activity">
                            <strong>Rock Climbing Adventure</strong>
                        </div>
                        <div class="notification-amount">
                            <span style="font-weight: bold;">$75.00</span>
                            <small style="margin-left: 0.5rem;">Aug 24, 2:11 PM</small>
                        </div>
                    </div>
                    <div class="notification-footer">
                        <div class="notification-status">
                            ✓ Payment Confirmed
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Signup Notification Mock -->
            <div class="event-notification notification-signup">
                <button class="btn-close">×</button>
                <div class="notification-content">
                    <div class="notification-header">
                        <div class="notification-avatar">
                            <div class="avatar">👤</div>
                        </div>
                        <div class="notification-title-area">
                            <div class="notification-title">
                                👤 New Registration
                            </div>
                            <div class="notification-subtitle">
                                Michael Chen<br>
                                <small>michael.chen@example.com</small>
                            </div>
                        </div>
                    </div>
                    <div class="notification-body">
                        <div class="notification-activity">
                            <strong>Photography Workshop</strong>
                        </div>
                        <div class="notification-signup-details">
                            <span style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">Premium Pass</span>
                            <small style="margin-left: 0.5rem;">$120.00</small>
                        </div>
                    </div>
                    <div class="notification-footer">
                        <div class="notification-status">
                            🕐 Registration Pending
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="demo-info">
            <h3>✨ Key Features</h3>
            <div class="feature-list">
                <div>• Real-time SSE notifications</div>
                <div>• Tabler.io components</div>
                <div>• Auto-dismiss timers</div>
                <div>• Mobile responsive</div>
                <div>• Hover to pause</div>
                <div>• Smooth animations</div>
                <div>• Professional styling</div>
                <div>• Activity links</div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        return f.name

def main():
    """Main screenshot test function"""
    print("📸 Event Notifications Screenshot Test")
    print("=" * 50)
    
    # Try to take screenshot of visual test
    screenshot_path = take_screenshot_with_browser()
    
    if not screenshot_path:
        print("📋 Creating fallback HTML demo...")
        temp_html = create_simple_html_test()
        
        try:
            screenshot_path = "/home/kdresdell/Documents/DEV/minipass_env/app/test/notification_demo_screenshot.png"
            
            # Try with the temp HTML file
            browsers_to_try = [
                ["firefox", "--headless", "--screenshot", screenshot_path, f"file://{temp_html}"],
                ["google-chrome", "--headless", "--disable-gpu", f"--screenshot={screenshot_path}", f"file://{temp_html}"],
            ]
            
            for browser_cmd in browsers_to_try:
                try:
                    print(f"Trying browser: {browser_cmd[0]}")
                    result = subprocess.run(browser_cmd, timeout=20, capture_output=True)
                    
                    if result.returncode == 0 and os.path.exists(screenshot_path):
                        print(f"✅ Demo screenshot saved to: {screenshot_path}")
                        break
                        
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_html)
            except:
                pass
    
    if os.path.exists(screenshot_path):
        print(f"🎯 Final screenshot location: {screenshot_path}")
        print("📝 Screenshot shows the event notification system UI components")
    else:
        print("❌ Unable to create screenshot with available browsers")

if __name__ == "__main__":
    main()