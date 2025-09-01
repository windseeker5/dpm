#!/usr/bin/env python3
"""
Test script to verify KPI card layouts on desktop and mobile
"""
import asyncio
from playwright.async_api import async_playwright
import sys

async def test_kpi_layout():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        
        # Test Desktop Layout
        print("=== Testing Desktop Layout ===")
        desktop_context = await browser.new_context(viewport={'width': 1200, 'height': 800})
        desktop_page = await desktop_context.new_page()
        
        try:
            # Navigate and login
            await desktop_page.goto('http://localhost:5000')
            await desktop_page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await desktop_page.fill('input[name="password"]', 'admin123')
            await desktop_page.click('button[type="submit"]')
            
            # Wait for dashboard to load
            await desktop_page.wait_for_selector('.kpi-cards-wrapper', timeout=10000)
            
            # Check desktop layout
            kpi_wrapper = await desktop_page.query_selector('.kpi-cards-wrapper')
            if kpi_wrapper:
                # Get computed styles
                display_style = await desktop_page.evaluate('(element) => getComputedStyle(element).display', kpi_wrapper)
                grid_columns = await desktop_page.evaluate('(element) => getComputedStyle(element).gridTemplateColumns', kpi_wrapper)
                
                print(f"Desktop Display: {display_style}")
                print(f"Desktop Grid Columns: {grid_columns}")
                
                # Count visible cards
                cards = await desktop_page.query_selector_all('.kpi-card-mobile')
                print(f"Desktop Card Count: {len(cards)}")
                
                # Check if cards are in a row
                if len(cards) >= 2:
                    card1_box = await cards[0].bounding_box()
                    card2_box = await cards[1].bounding_box()
                    
                    if card1_box and card2_box:
                        same_row = abs(card1_box['y'] - card2_box['y']) < 10
                        print(f"Desktop Cards in Same Row: {same_row}")
                        print(f"Card 1 Y: {card1_box['y']}, Card 2 Y: {card2_box['y']}")
            
        except Exception as e:
            print(f"Desktop test error: {e}")
        
        await desktop_context.close()
        
        # Test Mobile Layout
        print("\n=== Testing Mobile Layout ===")
        mobile_context = await browser.new_context(viewport={'width': 375, 'height': 667})
        mobile_page = await mobile_context.new_page()
        
        try:
            # Navigate and login
            await mobile_page.goto('http://localhost:5000')
            await mobile_page.fill('input[name="email"]', 'kdresdell@gmail.com')
            await mobile_page.fill('input[name="password"]', 'admin123')
            await mobile_page.click('button[type="submit"]')
            
            # Wait for dashboard to load
            await mobile_page.wait_for_selector('.kpi-cards-wrapper', timeout=10000)
            
            # Check mobile layout
            kpi_wrapper = await mobile_page.query_selector('.kpi-cards-wrapper')
            if kpi_wrapper:
                # Get computed styles
                display_style = await mobile_page.evaluate('(element) => getComputedStyle(element).display', kpi_wrapper)
                overflow_x = await mobile_page.evaluate('(element) => getComputedStyle(element).overflowX', kpi_wrapper)
                flex_direction = await mobile_page.evaluate('(element) => getComputedStyle(element).flexDirection', kpi_wrapper)
                
                print(f"Mobile Display: {display_style}")
                print(f"Mobile Overflow X: {overflow_x}")
                print(f"Mobile Flex Direction: {flex_direction}")
                
                # Count visible cards
                cards = await mobile_page.query_selector_all('.kpi-card-mobile')
                print(f"Mobile Card Count: {len(cards)}")
                
                # Check if cards are horizontally scrollable
                scroll_width = await mobile_page.evaluate('(element) => element.scrollWidth', kpi_wrapper)
                client_width = await mobile_page.evaluate('(element) => element.clientWidth', kpi_wrapper)
                
                print(f"Mobile Scroll Width: {scroll_width}")
                print(f"Mobile Client Width: {client_width}")
                print(f"Mobile Horizontally Scrollable: {scroll_width > client_width}")
            
        except Exception as e:
            print(f"Mobile test error: {e}")
        
        await mobile_context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_kpi_layout())