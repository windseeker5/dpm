#!/usr/bin/env python3
"""
Unit tests for collapsible notes feature in passport form.
Tests form functionality with and without notes, ensuring the feature works correctly.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Admin, Activity, PassportType, User, Passport

class TestCollapsibleNotes(unittest.TestCase):
    """Test cases for collapsible notes functionality"""
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Create tables
        db.create_all()
        
        # Create test admin
        admin = Admin(
            email='test@example.com',
            name='Test Admin'
        )
        admin.set_password('password')
        db.session.add(admin)
        
        # Create test activity
        activity = Activity(
            name='Test Activity',
            price_per_user=50.0,
            sessions_included=5,
            admin_id=1
        )
        db.session.add(activity)
        
        # Create test passport type
        passport_type = PassportType(
            name='Test Type',
            type='permanent',
            price_per_user=50.0,
            sessions_included=5,
            activity_id=1
        )
        db.session.add(passport_type)
        
        db.session.commit()
        
        # Login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password'
        })
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    def test_create_passport_form_loads(self):
        """Test that the create passport form loads with collapsible notes"""
        response = self.app.get('/create-passport?activity_id=1')
        self.assertEqual(response.status_code, 200)
        
        # Check that the collapsible notes structure is present
        response_data = response.get_data(as_text=True)
        self.assertIn('notes-header', response_data)
        self.assertIn('notes-collapse', response_data)
        self.assertIn('notes-chevron', response_data)
        self.assertIn('toggleNotes()', response_data)
        self.assertIn('ti-chevron-down', response_data)
    
    def test_create_passport_without_notes(self):
        """Test creating a passport without notes (notes field empty)"""
        response = self.app.post('/create-passport', data={
            'user_name': 'Test User',
            'user_email': 'user@test.com',
            'phone_number': '1234567890',
            'activity_id': 1,
            'passport_type_id': 1,
            'sold_amt': '50.00',
            'uses_remaining': '5',
            'notes': ''  # Empty notes
        })
        
        # Should redirect to success page or passport list
        self.assertIn(response.status_code, [200, 302])
        
        # Verify passport was created without notes
        passport = Passport.query.first()
        self.assertIsNotNone(passport)
        self.assertEqual(passport.notes, '')
    
    def test_create_passport_with_notes(self):
        """Test creating a passport with notes (notes field filled)"""
        response = self.app.post('/create-passport', data={
            'user_name': 'Test User 2',
            'user_email': 'user2@test.com',
            'phone_number': '1234567891',
            'activity_id': 1,
            'passport_type_id': 1,
            'sold_amt': '50.00',
            'uses_remaining': '5',
            'notes': 'Test notes content'
        })
        
        # Should redirect to success page or passport list
        self.assertIn(response.status_code, [200, 302])
        
        # Verify passport was created with notes
        passport = Passport.query.filter_by(notes='Test notes content').first()
        self.assertIsNotNone(passport)
        self.assertEqual(passport.notes, 'Test notes content')
    
    def test_javascript_function_exists(self):
        """Test that the toggleNotes JavaScript function is included"""
        response = self.app.get('/create-passport?activity_id=1')
        response_data = response.get_data(as_text=True)
        
        # Check for JavaScript function
        self.assertIn('function toggleNotes()', response_data)
        self.assertIn('notes-collapse', response_data)
        self.assertIn('notes-chevron', response_data)
    
    def test_css_styles_included(self):
        """Test that the CSS styles for collapsible notes are included"""
        response = self.app.get('/create-passport?activity_id=1')
        response_data = response.get_data(as_text=True)
        
        # Check for CSS classes
        self.assertIn('.notes-header', response_data)
        self.assertIn('.notes-chevron', response_data)
        self.assertIn('.notes-collapse', response_data)
        self.assertIn('transition:', response_data)

if __name__ == '__main__':
    unittest.main()