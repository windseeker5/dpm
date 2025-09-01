"""
Test KPI Cards Final Implementation
Tests the fixed KPI cards without debug styling and with proper dropdown z-index
"""
import unittest
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Admin
import subprocess
import time

class TestKPICardsFinal(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_kpi_cards_no_debug_borders(self):
        """Test that KPI cards don't have debug borders"""
        with self.app.app_context():
            # Login as admin
            with self.client.session_transaction() as sess:
                admin = Admin.query.filter_by(email='kdresdell@gmail.com').first()
                if admin:
                    sess['admin_id'] = admin.id
            
            # Get dashboard
            response = self.client.get('/dashboard')
            self.assertEqual(response.status_code, 200)
            
            # Check that ugly borders are not in the HTML
            html_content = response.data.decode('utf-8')
            
            # Verify no red border debug styling
            self.assertNotIn('border: 2px solid red', html_content, 
                           "Found ugly red debug border in HTML")
            
            # Verify no blue border debug styling  
            self.assertNotIn('border: 2px solid blue', html_content,
                           "Found ugly blue debug border in HTML")
            
            # Verify KPI cards structure is present
            self.assertIn('kpi-cards-wrapper', html_content)
            self.assertIn('kpi-card-mobile', html_content)
            
    def test_dropdown_z_index_css(self):
        """Test that dropdown z-index is properly set in CSS"""
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                admin = Admin.query.filter_by(email='kdresdell@gmail.com').first()
                if admin:
                    sess['admin_id'] = admin.id
            
            response = self.client.get('/dashboard')
            html_content = response.data.decode('utf-8')
            
            # Check for z-index styling in CSS
            self.assertIn('z-index: 1050', html_content, 
                         "Dropdown menu z-index not found")
            self.assertIn('z-index: 1040', html_content,
                         "Dropdown toggle z-index not found")
            
    def test_kpi_data_structure(self):
        """Test that KPI data is properly structured"""
        with self.app.app_context():
            with self.client.session_transaction() as sess:
                admin = Admin.query.filter_by(email='kdresdell@gmail.com').first()
                if admin:
                    sess['admin_id'] = admin.id
            
            response = self.client.get('/dashboard')
            html_content = response.data.decode('utf-8')
            
            # Verify all 4 KPI cards are present
            kpi_titles = ['REVENUE', 'ACTIVE PASSPORTS', 'PASSPORTS CREATED', 'UNPAID PASSPORTS']
            for title in kpi_titles:
                self.assertIn(title, html_content, f"KPI card '{title}' not found")
            
            # Verify dropdown options are present
            dropdown_options = ['Last 7 days', 'Last 30 days', 'Last 90 days', 'All time']
            for option in dropdown_options:
                self.assertIn(option, html_content, f"Dropdown option '{option}' not found")

if __name__ == '__main__':
    unittest.main()