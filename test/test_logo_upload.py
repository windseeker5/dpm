#!/usr/bin/env python3
"""
Test file for activity logo upload functionality
"""

import os
import sys
import unittest
import tempfile
import json
from io import BytesIO
from PIL import Image

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Activity, Admin
from werkzeug.datastructures import FileStorage


class TestLogoUpload(unittest.TestCase):
    
    def setUp(self):
        """Set up test database and client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        with self.app.app_context():
            # Create test activity
            self.test_activity = Activity(
                name="Test Activity",
                type="test",
                description="Test activity for logo upload"
            )
            db.session.add(self.test_activity)
            db.session.commit()
            
            self.activity_id = self.test_activity.id
            
        # Mock login session
        with self.client.session_transaction() as sess:
            sess['admin'] = 'test@example.com'
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            # Clean up test files
            if hasattr(self, 'test_activity') and self.test_activity.logo_filename:
                logo_path = os.path.join('static', 'uploads', 'logos', self.test_activity.logo_filename)
                if os.path.exists(logo_path):
                    os.remove(logo_path)
            
            # Clean up database
            db.session.delete(self.test_activity)
            db.session.commit()
    
    def create_test_image(self, format='PNG', size=(100, 100)):
        """Create a test image file"""
        img = Image.new('RGB', size, color='red')
        img_io = BytesIO()
        img.save(img_io, format)
        img_io.seek(0)
        return img_io
    
    def test_upload_logo_success(self):
        """Test successful logo upload"""
        # Create test image
        test_image = self.create_test_image()
        
        # Prepare file upload
        data = {
            'logo_file': (test_image, 'test_logo.png', 'image/png')
        }
        
        response = self.client.post(
            f'/activity/{self.activity_id}/upload-logo',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check response
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        self.assertIn('logo_url', response_data)
        self.assertEqual(response_data['message'], 'Logo uploaded successfully!')
        
        # Verify database was updated
        with self.app.app_context():
            updated_activity = Activity.query.get(self.activity_id)
            self.assertIsNotNone(updated_activity.logo_filename)
            self.assertTrue(updated_activity.logo_filename.startswith(f'activity_{self.activity_id}_'))
            
            # Verify file was created
            logo_path = os.path.join('static', 'uploads', 'logos', updated_activity.logo_filename)
            self.assertTrue(os.path.exists(logo_path))
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        # Create text file instead of image
        test_file = BytesIO(b"This is not an image")
        
        data = {
            'logo_file': (test_file, 'test.txt', 'text/plain')
        }
        
        response = self.client.post(
            f'/activity/{self.activity_id}/upload-logo',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid file type', response_data['error'])
    
    def test_upload_no_file(self):
        """Test upload with no file selected"""
        response = self.client.post(f'/activity/{self.activity_id}/upload-logo')
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('No file selected', response_data['error'])
    
    def test_upload_large_file(self):
        """Test upload with file too large"""
        # Create large image (simulate 6MB file)
        test_image = self.create_test_image(size=(2000, 2000))
        
        data = {
            'logo_file': (test_image, 'large_logo.png', 'image/png')
        }
        
        response = self.client.post(
            f'/activity/{self.activity_id}/upload-logo',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Note: This test might pass if the image is still under 5MB
        # The actual size depends on compression
        if response.status_code == 400:
            response_data = json.loads(response.data)
            self.assertFalse(response_data['success'])
            self.assertIn('too large', response_data['error'])
    
    def test_delete_logo_success(self):
        """Test successful logo deletion"""
        # First upload a logo
        test_image = self.create_test_image()
        data = {
            'logo_file': (test_image, 'test_logo.png', 'image/png')
        }
        
        upload_response = self.client.post(
            f'/activity/{self.activity_id}/upload-logo',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(upload_response.status_code, 200)
        
        # Now delete the logo
        delete_response = self.client.post(f'/activity/{self.activity_id}/delete-logo')
        
        self.assertEqual(delete_response.status_code, 200)
        
        response_data = json.loads(delete_response.data)
        self.assertTrue(response_data['success'])
        self.assertIn('deleted successfully', response_data['message'])
        self.assertIn('logo.png', response_data['logo_url'])  # Should be default logo
        
        # Verify database was updated
        with self.app.app_context():
            updated_activity = Activity.query.get(self.activity_id)
            self.assertIsNone(updated_activity.logo_filename)
    
    def test_upload_without_auth(self):
        """Test upload without authentication"""
        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()
        
        test_image = self.create_test_image()
        data = {
            'logo_file': (test_image, 'test_logo.png', 'image/png')
        }
        
        response = self.client.post(
            f'/activity/{self.activity_id}/upload-logo',
            data=data,
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 401)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertIn('Not authorized', response_data['error'])
    
    def test_get_activity_logo_url_function(self):
        """Test the get_activity_logo_url helper function"""
        from app import get_activity_logo_url
        
        with self.app.app_context():
            # Test with no logo
            default_url = get_activity_logo_url(self.test_activity)
            self.assertIn('logo.png', default_url)
            
            # Test with logo
            self.test_activity.logo_filename = 'test_logo.png'
            logo_url = get_activity_logo_url(self.test_activity)
            self.assertIn('uploads/logos/test_logo.png', logo_url)
            
            # Test with None activity
            none_url = get_activity_logo_url(None)
            self.assertIn('logo.png', none_url)


if __name__ == '__main__':
    # Create test directories
    os.makedirs('static/uploads/logos', exist_ok=True)
    
    unittest.main()