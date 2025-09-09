"""
Unit tests for Phase 3 hosted image system
Tests QR code optimization, image URL generation, and template integration
"""

import unittest
import sys
import os
import tempfile

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestPhase3HostedImages(unittest.TestCase):
    """Test the Phase 3 hosted image improvements"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures"""
        self.app_context.pop()

    def test_qr_code_optimization(self):
        """Test that optimized QR codes are smaller and properly sized"""
        from utils import generate_optimized_qr_code, generate_qr_code_image
        
        test_code = "TEST123456789"
        
        # Generate optimized QR code
        try:
            optimized_qr = generate_optimized_qr_code(test_code)
            optimized_data = optimized_qr.read()
            
            # Test that it generates data
            self.assertGreater(len(optimized_data), 0, "Optimized QR code should generate data")
            
            # Test that it's smaller than 15KB (much smaller than original ~50KB)
            self.assertLess(len(optimized_data), 15000, f"Optimized QR code too large: {len(optimized_data)} bytes")
            
            print(f"✅ Optimized QR code size: {len(optimized_data):,} bytes")
            
        except ImportError:
            print("⚠️ PIL not available, using fallback QR generation")
            # Test fallback method
            fallback_qr = generate_qr_code_image(test_code)
            fallback_data = fallback_qr.read()
            self.assertGreater(len(fallback_data), 0, "Fallback QR code should work")

    def test_image_url_generation(self):
        """Test image URL generation for different contexts"""
        from utils import generate_image_urls
        
        # Test with QR code context
        context1 = {
            'pass_code': 'TEST123',
            'activity_id': 5,
        }
        base_url = 'https://test.minipass.me'
        
        urls = generate_image_urls(context1, base_url)
        
        # Should generate QR code URL
        self.assertIn('qr_code_url', urls, "Should generate QR code URL")
        self.assertTrue(urls['qr_code_url'].startswith(base_url), "QR URL should use correct base URL")
        self.assertIn('qr/TEST123.png', urls['qr_code_url'], "QR URL should include pass code")
        
        print(f"✅ Generated QR URL: {urls['qr_code_url']}")
        
        # Test empty context
        empty_urls = generate_image_urls({}, base_url)
        self.assertEqual(len(empty_urls), 0, "Empty context should generate no URLs")

    def test_qr_code_caching(self):
        """Test that QR codes are cached to disk"""
        from utils import get_or_create_qr_code_url
        import os
        
        test_code = "CACHE_TEST_123"
        base_url = "https://test.minipass.me"
        
        # First call should create the file
        url1 = get_or_create_qr_code_url(test_code, base_url)
        
        # Check file was created
        expected_path = f'static/uploads/qr/{test_code}.png'
        self.assertTrue(os.path.exists(expected_path), "QR code file should be created")
        
        # Second call should return cached version
        url2 = get_or_create_qr_code_url(test_code, base_url)
        self.assertEqual(url1, url2, "Cached QR code should return same URL")
        
        # Clean up test file
        if os.path.exists(expected_path):
            os.remove(expected_path)
        
        print(f"✅ QR code caching working: {url1}")

    def test_directory_structure_exists(self):
        """Test that hosted image directories were created"""
        directories = [
            'static/uploads/qr',
            'static/uploads/heroes',
            'static/uploads/logos',
            'static/uploads/email_assets'
        ]
        
        for directory in directories:
            self.assertTrue(os.path.exists(directory), f"Directory should exist: {directory}")
            self.assertTrue(os.path.isdir(directory), f"Should be a directory: {directory}")
        
        print("✅ All hosted image directories exist")

    def test_template_compilation_success(self):
        """Test that newPass template compiled with hosted images"""
        template_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/newPass_compiled/index.html"
        
        try:
            with open(template_path, 'r') as f:
                compiled_content = f.read()
            
            # Check that template uses hosted URLs instead of cid:
            self.assertIn('{{ qr_code_url }}', compiled_content, 
                         "Compiled template should use QR code URL")
            self.assertIn('hero_image_url', compiled_content,
                         "Compiled template should use hero image URL")
            
            # Check that old cid references are gone
            self.assertNotIn('cid:qr_code', compiled_content,
                           "Compiled template should not have cid:qr_code")
            
            # Check QR code size optimization (200x200 instead of 360x360)
            self.assertIn('width="200" height="200"', compiled_content,
                         "QR code should be optimized to 200x200px")
            
            print("✅ Template compilation successful with hosted images")
            
        except FileNotFoundError:
            self.fail("Compiled newPass template not found")

    def test_send_email_hosted_mode(self):
        """Test send_email function with hosted images enabled"""
        # This is a dry run test - we don't actually send email
        # Just test that the function can handle hosted image mode
        
        from utils import generate_image_urls
        
        # Simulate what send_email does
        context = {
            'pass_code': 'TEST123',
            'activity_id': 5,
        }
        base_url = 'https://test.minipass.me'
        
        # Test the image URL generation that send_email uses
        image_urls = generate_image_urls(context, base_url)
        context.update(image_urls)
        
        # Verify context now has image URLs
        self.assertIn('qr_code_url', context, "Context should have QR code URL")
        
        print("✅ send_email hosted mode preparation working")


if __name__ == '__main__':
    unittest.main()