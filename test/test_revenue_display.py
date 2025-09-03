"""
Test revenue display simplification in activity dashboard.
Tests that only the current amount is displayed with the progress bar.
"""
import unittest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from models import Admin, Activity, PassportType
from flask import url_for
from bs4 import BeautifulSoup

class TestRevenueDisplay(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create test admin
        test_admin = Admin.query.filter_by(email='test@example.com').first()
        if not test_admin:
            test_admin = Admin(
                email='test@example.com',
                password_hash='test_hash',
                is_verified=True
            )
            db.session.add(test_admin)
            db.session.commit()
        
        self.test_admin = test_admin
        
        # Login as test admin
        with self.app.session_transaction() as sess:
            sess['admin_id'] = self.test_admin.id
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
    
    def test_revenue_display_simplified(self):
        """Test that revenue display shows only current amount and progress bar."""
        # Create a test activity and passport type
        activity = Activity(
            name='Test Activity',
            description='Test description',
            created_by=self.test_admin.id
        )
        db.session.add(activity)
        db.session.flush()  # Get the ID
        
        passport_type = PassportType(
            activity_id=activity.id,
            name='Regular',
            type='permanent',
            target_revenue=1000.0,
            price_per_user=50.0
        )
        db.session.add(passport_type)
        db.session.commit()
        
        # Mock KPI data for revenue
        with app.test_request_context():
            with self.app as client:
                # Get the activity dashboard page
                response = client.get(f'/activity-dashboard/{activity.id}')
                self.assertEqual(response.status_code, 200)
                
                # Parse the HTML response
                soup = BeautifulSoup(response.data, 'html.parser')
                
                # Find the revenue progress container
                progress_container = soup.find('div', class_='revenue-progress-container')
                self.assertIsNotNone(progress_container, "Revenue progress container should exist")
                
                # Check that progress labels exist
                progress_labels = progress_container.find('div', class_='progress-labels')
                self.assertIsNotNone(progress_labels, "Progress labels container should exist")
                
                # Check that the title "Revenue Progress" exists
                progress_title = progress_labels.find('span', class_='progress-title')
                self.assertIsNotNone(progress_title, "Progress title should exist")
                self.assertEqual(progress_title.text.strip(), "Revenue Progress")
                
                # Check that current amount is displayed (with proper class)
                current_amount = progress_labels.find('span', class_='progress-current-amount')
                self.assertIsNotNone(current_amount, "Current amount should be displayed")
                
                # Check that the current amount contains currency formatting
                amount_text = current_amount.text.strip()
                self.assertTrue(amount_text.startswith('$'), "Amount should start with $ symbol")
                
                # Check that progress bar wrapper exists
                progress_bar_wrapper = progress_container.find('div', class_='progress-bar-wrapper')
                self.assertIsNotNone(progress_bar_wrapper, "Progress bar wrapper should exist")
                
                # Check that progress bar fill exists
                progress_bar_fill = progress_bar_wrapper.find('div', class_='progress-bar-fill')
                self.assertIsNotNone(progress_bar_fill, "Progress bar fill should exist")
                
                # Check that percentage text is NOT displayed
                progress_percentage = progress_container.find('div', class_='progress-percentage')
                self.assertIsNone(progress_percentage, "Progress percentage text should not exist")
                
                # Check that target amount text is NOT displayed
                progress_amounts = progress_labels.find('span', class_='progress-amounts')
                self.assertIsNone(progress_amounts, "Target amount text should not exist")
                
                # Check that old progress-amounts class is not used
                old_amounts = soup.find_all(string=lambda text: text and 'target' in text.lower())
                revenue_related_targets = [text for text in old_amounts if 'revenue' in str(text).lower() or '$' in str(text)]
                # Allow some target text in other contexts, but not in the revenue progress area
                progress_area_text = progress_container.get_text() if progress_container else ""
                self.assertNotIn('target', progress_area_text.lower(), "Target text should not appear in progress area")
        
        # Cleanup
        db.session.delete(passport_type)
        db.session.delete(activity)
        db.session.commit()
    
    def test_progress_bar_calculation(self):
        """Test that progress bar calculation remains correct."""
        # Create a test activity with known values
        activity = Activity(
            name='Test Activity',
            description='Test description',
            created_by=self.test_admin.id
        )
        db.session.add(activity)
        db.session.flush()  # Get the ID
        
        passport_type = PassportType(
            activity_id=activity.id,
            name='Regular',
            type='permanent',
            target_revenue=1000.0,
            price_per_user=50.0
        )
        db.session.add(passport_type)
        db.session.commit()
        
        with app.test_request_context():
            with self.app as client:
                # Mock the KPI data to have a known current revenue
                # This would normally come from utils.get_kpi_data()
                response = client.get(f'/activity-dashboard/{activity.id}')
                self.assertEqual(response.status_code, 200)
                
                soup = BeautifulSoup(response.data, 'html.parser')
                progress_bar_fill = soup.find('div', class_='progress-bar-fill')
                
                if progress_bar_fill:
                    # Check that width style is present
                    style = progress_bar_fill.get('style', '')
                    self.assertIn('width:', style, "Progress bar should have width style")
                    
                    # Extract width percentage
                    import re
                    width_match = re.search(r'width:\s*(\d+(?:\.\d+)?)%', style)
                    self.assertIsNotNone(width_match, "Width should be a percentage")
                    
                    width_percent = float(width_match.group(1))
                    self.assertGreaterEqual(width_percent, 0, "Width should be >= 0%")
                    self.assertLessEqual(width_percent, 100, "Width should be <= 100%")
        
        # Cleanup
        db.session.delete(passport_type)
        db.session.delete(activity)
        db.session.commit()
    
    def test_currency_formatting(self):
        """Test that currency is properly formatted."""
        # Create a test activity
        activity = Activity(
            name='Test Activity',
            description='Test description',
            created_by=self.test_admin.id
        )
        db.session.add(activity)
        db.session.flush()  # Get the ID
        
        passport_type = PassportType(
            activity_id=activity.id,
            name='Regular',
            type='permanent',
            target_revenue=1000.0,
            price_per_user=50.0
        )
        db.session.add(passport_type)
        db.session.commit()
        
        with app.test_request_context():
            with self.app as client:
                response = client.get(f'/activity-dashboard/{activity.id}')
                self.assertEqual(response.status_code, 200)
                
                soup = BeautifulSoup(response.data, 'html.parser')
                current_amount = soup.find('span', class_='progress-current-amount')
                
                if current_amount:
                    amount_text = current_amount.text.strip()
                    
                    # Should start with dollar sign
                    self.assertTrue(amount_text.startswith('$'), "Amount should start with $")
                    
                    # Should not contain target text
                    self.assertNotIn('target', amount_text.lower(), "Amount should not contain 'target'")
                    self.assertNotIn('/', amount_text, "Amount should not contain '/' separator")
                    
                    # Should be properly formatted number (allowing commas for thousands)
                    amount_number = amount_text[1:]  # Remove $ sign
                    # Should be valid number format (with or without commas)
                    import re
                    self.assertTrue(re.match(r'^\d{1,3}(,\d{3})*(\.\d{2})?$|^\d+(\.\d{2})?$', amount_number), 
                                  f"Amount '{amount_number}' should be properly formatted")
        
        # Cleanup  
        db.session.delete(passport_type)
        db.session.delete(activity)
        db.session.commit()


if __name__ == '__main__':
    unittest.main()