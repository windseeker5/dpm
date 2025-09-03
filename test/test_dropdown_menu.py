import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Admin, Activity


class TestDropdownMenu(unittest.TestCase):
    """Test cases for the mobile dropdown menu functionality."""

    def setUp(self):
        """Set up test fixtures."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test admin
        self.admin = Admin(
            email='kdresdell@gmail.com',
            name='Test Admin'
        )
        self.admin.set_password('admin123')
        db.session.add(self.admin)
        
        # Create test activity
        self.activity = Activity(
            name='Test Activity',
            description='Test activity description',
            location='Test Location',
            target_revenue=1000.0,
            admin_id=1
        )
        db.session.add(self.activity)
        db.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        """Helper method to log in as test admin."""
        return self.app.post('/login', data={
            'email': 'kdresdell@gmail.com',
            'password': 'admin123'
        }, follow_redirects=True)

    def test_dropdown_elements_in_template(self):
        """Test that dropdown elements are present in the activity dashboard template."""
        self.login()
        response = self.app.get(f'/activity/{self.activity.id}')
        
        self.assertEqual(response.status_code, 200)
        html_content = response.data.decode('utf-8')
        
        # Check mobile dropdown exists
        self.assertIn('dropdown d-md-none', html_content)
        self.assertIn('data-bs-toggle="dropdown"', html_content)
        self.assertIn('dropdown-menu dropdown-menu-end', html_content)
        
        # Check desktop buttons exist
        self.assertIn('activity-actions d-none d-md-flex', html_content)
        
        # Check all menu items are present
        self.assertIn('ti-edit', html_content)
        self.assertIn('ti-mail', html_content) 
        self.assertIn('ti-scan', html_content)
        self.assertIn('ti-plus', html_content)
        self.assertIn('ti-trash', html_content)

    def test_dropdown_menu_items_functionality(self):
        """Test that all dropdown menu items have correct links and functionality."""
        self.login()
        response = self.app.get(f'/activity/{self.activity.id}')
        
        html_content = response.data.decode('utf-8')
        
        # Check Edit link
        self.assertIn(f'href="/edit_activity/{self.activity.id}"', html_content)
        
        # Check Email Templates link
        self.assertIn(f'href="/email_template_customization/{self.activity.id}"', html_content)
        
        # Check Scan link
        self.assertIn('href="/scan_qr"', html_content)
        
        # Check Create Passport link
        self.assertIn(f'href="/create_passport/{self.activity.id}"', html_content)
        
        # Check Delete functionality (onclick)
        self.assertIn('checkAndDeleteActivity', html_content)

    def test_responsive_classes(self):
        """Test that responsive classes are correctly applied."""
        self.login()
        response = self.app.get(f'/activity/{self.activity.id}')
        
        html_content = response.data.decode('utf-8')
        
        # Mobile dropdown should be hidden on medium and up
        self.assertIn('d-md-none', html_content)
        
        # Desktop buttons should be hidden on small screens
        self.assertIn('d-none d-md-flex', html_content)

    def test_dropdown_icon_svg(self):
        """Test that the three-dots icon SVG is present."""
        self.login()
        response = self.app.get(f'/activity/{self.activity.id}')
        
        html_content = response.data.decode('utf-8')
        
        # Check for three-dots icon SVG elements
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', html_content)
        self.assertIn('circle cx="12" cy="12"', html_content)
        self.assertIn('circle cx="12" cy="19"', html_content)
        self.assertIn('circle cx="12" cy="5"', html_content)

    def test_dropdown_menu_structure(self):
        """Test that the dropdown menu has proper structure with dividers."""
        self.login()
        response = self.app.get(f'/activity/{self.activity.id}')
        
        html_content = response.data.decode('utf-8')
        
        # Check for dropdown dividers
        self.assertIn('dropdown-divider', html_content)
        
        # Check for text-danger class on delete item
        self.assertIn('dropdown-item text-danger', html_content)

    def test_activity_actions_are_duplicated_correctly(self):
        """Test that all actions exist in both mobile dropdown and desktop buttons."""
        self.login()
        response = self.app.get(f'/activity/{self.activity.id}')
        
        html_content = response.data.decode('utf-8')
        
        # Each action should appear twice (once in dropdown, once in desktop)
        actions = ['ti-edit', 'ti-mail', 'ti-scan', 'ti-plus', 'ti-trash']
        
        for action in actions:
            # Count occurrences (should be at least 2)
            count = html_content.count(action)
            self.assertGreaterEqual(count, 2, f"Action {action} should appear at least twice")


if __name__ == '__main__':
    unittest.main()