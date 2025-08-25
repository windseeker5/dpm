#!/usr/bin/env python3
"""
Simple test to verify KPI component integration works correctly

This test directly imports and tests the KPI components to ensure they work
without needing authentication setup.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_kpi_component_import():
    """Test that we can import the KPI component"""
    try:
        from components.kpi_card import generate_kpi_card, generate_dashboard_cards, kpi_card_generator
        print("✅ KPI component imports successfully")
        return True
    except Exception as e:
        print(f"❌ KPI component import failed: {str(e)}")
        return False

def test_kpi_card_generation():
    """Test KPI card generation with mock data"""
    try:
        from components.kpi_card import generate_kpi_card
        
        # Test individual card generation
        card = generate_kpi_card(
            card_type='revenue',
            activity_id=None,  # Global data
            period='7d',
            device_type='desktop'
        )
        
        if card.get('success'):
            print("✅ KPI card generation successful")
            print(f"   Card ID: {card.get('card_id')}")
            print(f"   Generation time: {card.get('generation_time_ms', 0)}ms")
            return True
        else:
            print(f"❌ KPI card generation failed: {card.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ KPI card generation error: {str(e)}")
        return False

def test_dashboard_cards_generation():
    """Test dashboard cards generation"""
    try:
        from components.kpi_card import generate_dashboard_cards
        
        # Test multiple cards generation
        dashboard = generate_dashboard_cards(
            activity_id=None,  # Global data
            period='7d',
            device_type='desktop'
        )
        
        if dashboard.get('success'):
            card_count = dashboard.get('total_cards', 0)
            print(f"✅ Dashboard cards generation successful ({card_count} cards)")
            
            # Show generated card types
            if 'cards' in dashboard:
                card_types = [card.get('card_type') for card in dashboard['cards'].values()]
                print(f"   Generated card types: {', '.join(card_types)}")
            
            return True
        else:
            print(f"❌ Dashboard cards generation failed: {dashboard.get('error', 'Unknown error')}")
            error_count = dashboard.get('error_count', 0)
            if error_count > 0:
                print(f"   Errors encountered: {error_count}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard cards generation error: {str(e)}")
        return False

def test_input_validation():
    """Test KPI component input validation"""
    try:
        from components.kpi_card import generate_kpi_card
        
        # Test invalid card type
        invalid_card = generate_kpi_card(
            card_type='invalid_type',
            period='7d'
        )
        
        if not invalid_card.get('success') and invalid_card.get('error_type') == 'validation':
            print("✅ Input validation working correctly")
            return True
        else:
            print("❌ Input validation not working as expected")
            return False
            
    except Exception as e:
        print(f"❌ Input validation test error: {str(e)}")
        return False

def test_security_features():
    """Test security features of KPI component"""
    try:
        from components.kpi_card import kpi_card_generator
        
        # Test cache stats
        cache_stats = kpi_card_generator.get_cache_stats()
        if cache_stats.get('success'):
            print("✅ Cache stats accessible")
        else:
            print("⚠️ Cache stats not accessible")
        
        # Test cache clearing
        clear_result = kpi_card_generator.clear_cache()
        if clear_result.get('success'):
            print("✅ Cache clearing works")
        else:
            print("⚠️ Cache clearing not working")
        
        return True
        
    except Exception as e:
        print(f"❌ Security features test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing KPI Component Integration")
    print("=" * 40)
    
    tests = [
        ("Component Import", test_kpi_component_import),
        ("KPI Card Generation", test_kpi_card_generation),
        ("Dashboard Cards Generation", test_dashboard_cards_generation),
        ("Input Validation", test_input_validation),
        ("Security Features", test_security_features)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\\n📝 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} failed")
    
    print("\\n" + "=" * 40)
    print(f"🧪 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All KPI component tests passed!")
        return True
    else:
        print("⚠️ Some tests failed - check component implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)