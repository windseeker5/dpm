#!/usr/bin/env python3
"""Test script to verify the clean activity header implementation."""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def test_activity_header():
    """Test the activity header at different viewport sizes."""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Login first
        print("Logging in...")
        await page.goto("http://127.0.0.1:8890/login")
        await page.fill('input[name="email"]', 'kdresdell@gmail.com')
        await page.fill('input[name="password"]', 'admin123')
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard")
        
        # Navigate to activity dashboard
        print("Navigating to activity dashboard...")
        await page.goto("http://127.0.0.1:8890/activity/1")
        await page.wait_for_selector('.activity-header-clean', timeout=5000)
        
        # Test 1: Desktop view (1920x1080)
        print("\n=== Testing Desktop View (1920x1080) ===")
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.wait_for_timeout(1000)
        
        # Check if all elements are present
        elements_to_check = [
            ('.activity-subtitle-line', 'Activity subtitle line'),
            ('.badge-active', 'Active badge'),
            ('.pulse-dot', 'Pulse indicator'),
            ('.activity-title', 'Activity title'),
            ('.activity-description', 'Description'),
            ('.activity-stats-row', 'Stats row'),
            ('.revenue-progress-container', 'Revenue progress'),
            ('.progress-bar-fill', 'Progress bar fill'),
            ('.activity-actions', 'Action buttons'),
            ('.activity-image', 'Activity image')
        ]
        
        for selector, name in elements_to_check:
            element = await page.query_selector(selector)
            if element:
                print(f"✓ {name} found")
            else:
                print(f"✗ {name} NOT FOUND")
        
        # Check layout dimensions
        header = await page.query_selector('.activity-header-clean')
        if header:
            box = await header.bounding_box()
            print(f"\nHeader dimensions: {box['width']}x{box['height']}px")
        
        # Check split layout
        content_section = await page.query_selector('.content-section')
        image_section = await page.query_selector('.image-section')
        
        if content_section and image_section:
            content_box = await content_section.bounding_box()
            image_box = await image_section.bounding_box()
            print(f"Content section: {content_box['width']}px wide")
            print(f"Image section: {image_box['width']}px wide")
            ratio = content_box['width'] / (content_box['width'] + image_box['width']) * 100
            print(f"Content/Image ratio: {ratio:.1f}% / {100-ratio:.1f}%")
        
        # Take desktop screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop_screenshot = f"/home/kdresdell/Documents/DEV/minipass_env/app/playwright/activity_header_desktop_{timestamp}.png"
        await page.screenshot(path=desktop_screenshot, full_page=False)
        print(f"\nDesktop screenshot saved: {desktop_screenshot}")
        
        # Test 2: Mobile view (390x844 - iPhone 12 Pro)
        print("\n=== Testing Mobile View (390x844) ===")
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(1000)
        
        # Check if image is on top (order: -1 in CSS)
        mobile_image = await page.query_selector('.image-section')
        if mobile_image:
            image_box = await mobile_image.bounding_box()
            print(f"Mobile image position: top={image_box['y']}px")
            print(f"Mobile image dimensions: {image_box['width']}x{image_box['height']}px")
        
        # Check if stats are in grid layout
        stats_row = await page.query_selector('.activity-stats-row')
        if stats_row:
            stat_items = await stats_row.query_selector_all('.stat')
            print(f"Number of stat items: {len(stat_items)}")
            if len(stat_items) > 0:
                first_stat = await stat_items[0].bounding_box()
                print(f"First stat position: x={first_stat['x']}, y={first_stat['y']}")
        
        # Check if buttons are stacked
        buttons = await page.query_selector_all('.activity-actions .btn')
        if len(buttons) >= 2:
            btn1_box = await buttons[0].bounding_box()
            btn2_box = await buttons[1].bounding_box()
            if btn2_box['y'] > btn1_box['y']:
                print("✓ Buttons are stacked vertically")
            else:
                print("✗ Buttons are not stacked")
        
        # Take mobile screenshot
        mobile_screenshot = f"/home/kdresdell/Documents/DEV/minipass_env/app/playwright/activity_header_mobile_{timestamp}.png"
        await page.screenshot(path=mobile_screenshot, full_page=False)
        print(f"\nMobile screenshot saved: {mobile_screenshot}")
        
        # Test 3: Check revenue progress bar
        print("\n=== Testing Revenue Progress Bar ===")
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        progress_fill = await page.query_selector('.progress-bar-fill')
        if progress_fill:
            style = await progress_fill.get_attribute('style')
            print(f"Progress bar style: {style}")
            
            # Check if percentage is displayed
            percentage = await page.query_selector('.progress-percentage')
            if percentage:
                text = await percentage.inner_text()
                print(f"Progress percentage text: {text}")
        
        # Test 4: Check for gray dividers (should not exist)
        print("\n=== Checking for Gray Dividers ===")
        stat_items = await page.query_selector_all('.activity-stats-row .stat')
        for i, item in enumerate(stat_items):
            computed_style = await page.evaluate('''
                (element) => {
                    const styles = window.getComputedStyle(element);
                    return {
                        borderLeft: styles.borderLeft,
                        borderRight: styles.borderRight,
                        padding: styles.padding
                    };
                }
            ''', item)
            
            has_border = 'none' not in computed_style['borderLeft'] or 'none' not in computed_style['borderRight']
            if has_border:
                print(f"✗ Stat item {i} has border: {computed_style}")
            else:
                print(f"✓ Stat item {i} has no borders")
        
        await browser.close()
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_activity_header())