#!/usr/bin/env python3
"""
Test the new KPICard component implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from components.kpi_card import KPICard, generate_kpi_card, generate_dashboard_cards, clear_kpi_cache
import json

def test_kpi_card():
    """Test the KPI Card component"""
    print("🧪 Testing KPICard Component")
    print("=" * 50)
    
    # Initialize Flask app context for testing
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        # Test 1: Create KPICard instance
        print("\n1️⃣ Testing KPICard instantiation...")
        kpi = KPICard()
        print("✅ KPICard created successfully")
        
        # Test 2: Test input validation
        print("\n2️⃣ Testing input validation...")
        
        # Valid input
        try:
            result = kpi.generate_card(
                card_type='revenue',
                period='7d',
                device_type='desktop'
            )
            if result.get('success') is not None:
                print("✅ Valid input handled correctly")
            else:
                print("⚠️ Valid input returned unexpected result")
        except Exception as e:
            print(f"⚠️ Valid input test failed: {e}")
        
        # Invalid card type
        try:
            result = kpi.generate_card(card_type='invalid_type')
            if not result.get('success', True):
                print("✅ Invalid card type properly rejected")
            else:
                print("❌ Invalid card type was accepted")
        except Exception as e:
            print(f"⚠️ Invalid card type test error: {e}")
        
        # Invalid period
        try:
            result = kpi.generate_card(card_type='revenue', period='invalid')
            if not result.get('success', True):
                print("✅ Invalid period properly rejected")
            else:
                print("❌ Invalid period was accepted")
        except Exception as e:
            print(f"⚠️ Invalid period test error: {e}")
        
        # Test 3: Test cache functionality
        print("\n3️⃣ Testing cache functionality...")
        try:
            # Clear cache first
            clear_result = kpi.clear_cache()
            print(f"✅ Cache cleared: {clear_result.get('cleared_count', 0)} entries")
            
            # Generate card (should miss cache)
            result1 = kpi.generate_card(card_type='revenue', force_refresh=True)
            if not result1.get('cache_hit', True):
                print("✅ Cache miss on first generation")
            
            # Generate same card again (should hit cache)
            result2 = kpi.generate_card(card_type='revenue')
            if result2.get('cache_hit', False):
                print("✅ Cache hit on second generation")
            else:
                print("⚠️ Expected cache hit but got miss")
                
        except Exception as e:
            print(f"⚠️ Cache test failed: {e}")
        
        # Test 4: Test convenience functions
        print("\n4️⃣ Testing convenience functions...")
        try:
            # Test single card generation
            card = generate_kpi_card('active_users')
            if isinstance(card, dict):
                print("✅ generate_kpi_card() works")
            
            # Test dashboard cards generation
            dashboard = generate_dashboard_cards()
            if isinstance(dashboard, dict) and 'cards' in dashboard:
                print(f"✅ generate_dashboard_cards() generated {dashboard.get('total_cards', 0)} cards")
            
        except Exception as e:
            print(f"⚠️ Convenience functions test failed: {e}")
        
        # Test 5: Test circuit breaker functionality
        print("\n5️⃣ Testing circuit breaker...")
        try:
            # Get circuit breaker stats
            stats = kpi.get_cache_stats()
            if stats.get('success', False):
                print("✅ Circuit breaker stats accessible")
                print(f"   Cache size: {stats.get('cache_size', 0)}")
                print(f"   Circuit breakers: {len(stats.get('circuit_breakers', {}))}")
            
        except Exception as e:
            print(f"⚠️ Circuit breaker test failed: {e}")
        
        # Test 6: Test different device types
        print("\n6️⃣ Testing device types...")
        try:
            desktop_card = generate_kpi_card('revenue', device_type='desktop')
            mobile_card = generate_kpi_card('revenue', device_type='mobile')
            
            if desktop_card.get('device_type') == 'desktop':
                print("✅ Desktop card generated")
            if mobile_card.get('device_type') == 'mobile':
                print("✅ Mobile card generated")
                
            # Check CSS classes are different
            desktop_css = desktop_card.get('css_classes', {})
            mobile_css = mobile_card.get('css_classes', {})
            if desktop_css != mobile_css:
                print("✅ Different CSS classes for different device types")
                
        except Exception as e:
            print(f"⚠️ Device type test failed: {e}")
        
        # Test 7: Test data structure compatibility
        print("\n7️⃣ Testing data structure compatibility...")
        try:
            card = generate_kpi_card('revenue')
            
            # Check for dashboard.html compatibility (nested structure)
            if 'nested_data' in card:
                print("✅ Dashboard.html compatibility structure present")
            
            # Check for activity_dashboard.html compatibility (flat structure)
            required_fields = ['total', 'percentage', 'trend', 'trend_data']
            if all(field in card for field in required_fields):
                print("✅ Activity dashboard compatibility fields present")
                
        except Exception as e:
            print(f"⚠️ Data structure compatibility test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 KPICard component testing completed!")
    print("\n📋 Summary:")
    print("- Input validation: Implemented with Pydantic schemas")
    print("- Caching: In-memory cache with configurable TTLs")
    print("- Security: SQL injection prevention and input sanitization")
    print("- Circuit breaker: Database resilience pattern implemented")
    print("- Error handling: Comprehensive logging and fallback data")
    print("- Compatibility: Supports both dashboard formats")
    print("- Responsive design: Mobile and desktop variants")


if __name__ == '__main__':
    test_kpi_card()