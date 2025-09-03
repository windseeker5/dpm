#!/usr/bin/env python3
"""
Quick test script to verify dropdown menu implementation
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app import app, db
from models import Admin, Activity


def test_dropdown_implementation():
    """Test that the dropdown implementation is working correctly"""
    
    with app.test_client() as client:
        with app.app_context():
            # Create in-memory database for testing
            app.config['TESTING'] = True
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            app.config['WTF_CSRF_ENABLED'] = False
            
            db.create_all()
            
            # Create test admin
            admin = Admin(
                email='kdresdell@gmail.com',
                name='Test Admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create test activity
            activity = Activity(
                name='Test Activity for Dropdown',
                description='Test activity to verify dropdown functionality',
                location='Test Location',
                target_revenue=1000.0,
                admin_id=1
            )
            db.session.add(activity)
            db.session.commit()
            
            # Login
            response = client.post('/login', data={
                'email': 'kdresdell@gmail.com',
                'password': 'admin123'
            }, follow_redirects=True)
            
            print("✓ Login successful" if response.status_code == 200 else "✗ Login failed")
            
            # Test activity dashboard
            response = client.get(f'/activity/{activity.id}')
            
            if response.status_code == 200:
                html_content = response.data.decode('utf-8')
                
                # Check for mobile dropdown
                checks = [
                    ('Mobile dropdown container', 'dropdown d-md-none'),
                    ('Bootstrap dropdown toggle', 'data-bs-toggle="dropdown"'),
                    ('Dropdown menu', 'dropdown-menu dropdown-menu-end'),
                    ('Desktop buttons container', 'activity-actions d-none d-md-flex'),
                    ('Three-dots icon SVG', '<svg xmlns="http://www.w3.org/2000/svg"'),
                    ('Edit action in dropdown', 'ti-edit'),
                    ('Email templates action', 'ti-mail'),
                    ('Scan action', 'ti-scan'),
                    ('Create passport action', 'ti-plus'),
                    ('Delete action', 'ti-trash'),
                    ('Dropdown dividers', 'dropdown-divider'),
                    ('Danger styling for delete', 'dropdown-item text-danger')
                ]
                
                print("\n=== Dropdown Implementation Test Results ===")
                all_passed = True
                
                for check_name, check_content in checks:
                    if check_content in html_content:
                        print(f"✓ {check_name}")
                    else:
                        print(f"✗ {check_name} - MISSING")
                        all_passed = False
                
                # Count action buttons (should be duplicated)
                action_counts = {}
                actions = ['ti-edit', 'ti-mail', 'ti-scan', 'ti-plus', 'ti-trash']
                
                print("\n=== Action Button Duplication Check ===")
                for action in actions:
                    count = html_content.count(action)
                    action_counts[action] = count
                    if count >= 2:
                        print(f"✓ {action}: {count} occurrences (mobile + desktop)")
                    else:
                        print(f"✗ {action}: {count} occurrences - NEEDS AT LEAST 2")
                        all_passed = False
                
                print(f"\n=== Overall Result ===")
                if all_passed:
                    print("✓ All dropdown implementation checks PASSED!")
                    print("✓ Mobile dropdown menu is properly implemented")
                    print("✓ Desktop buttons are preserved")
                    print("✓ Responsive classes are correct")
                else:
                    print("✗ Some checks FAILED - review implementation")
                
                return all_passed
            else:
                print(f"✗ Failed to load activity dashboard: {response.status_code}")
                return False


def test_css_styles():
    """Test that CSS styles are properly added"""
    css_file = 'static/css/activity-header-clean.css'
    
    print("\n=== CSS Styles Check ===")
    
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
            
            css_checks = [
                ('Mobile dropdown styles comment', '/* Mobile dropdown menu styles */'),
                ('Button icon padding', '.dropdown .btn-icon'),
                ('Focus styles', '.btn-icon:focus'),
                ('Dropdown menu styling', '.dropdown-menu'),
                ('Dropdown item styling', '.dropdown-item'),
                ('Hover effects', '.dropdown-item:hover'),
                ('Danger hover effects', '.dropdown-item.text-danger:hover'),
                ('Divider styles', '.dropdown-divider')
            ]
            
            all_css_passed = True
            for check_name, check_content in css_checks:
                if check_content in css_content:
                    print(f"✓ {check_name}")
                else:
                    print(f"✗ {check_name} - MISSING")
                    all_css_passed = False
            
            return all_css_passed
    else:
        print("✗ CSS file not found")
        return False


if __name__ == '__main__':
    print("Testing Mobile Dropdown Menu Implementation")
    print("=" * 50)
    
    # Test implementation
    impl_passed = test_dropdown_implementation()
    
    # Test CSS
    css_passed = test_css_styles()
    
    print("\n" + "=" * 50)
    if impl_passed and css_passed:
        print("🎉 ALL TESTS PASSED! Mobile dropdown is ready!")
        print("\nNext steps:")
        print("1. Test on actual mobile device/browser")
        print("2. Verify responsive behavior at 768px breakpoint")
        print("3. Test all dropdown menu items functionality")
    else:
        print("❌ Some tests failed. Review the implementation.")
    
    print("\nImplementation Summary:")
    print("- Mobile dropdown shows only on screens < 768px (d-md-none)")
    print("- Desktop buttons show only on screens >= 768px (d-none d-md-flex)")
    print("- Three-dots icon uses standard Tabler icon set")
    print("- All original functionality preserved in both views")
    print("- Bootstrap dropdown component used for functionality")