"""
Unit tests for Email Template Modal fixes
Tests the modal backdrop and centering implementation.
"""

import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestEmailTemplateModal(unittest.TestCase):
    """Test email template modal implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = None
        
    def test_modal_has_blur_class(self):
        """Test that the modal has the modal-blur class for backdrop effect."""
        # Read the template file
        template_path = os.path.join(os.path.dirname(__file__), '../templates/email_template_customization.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Parse the HTML content
        soup = BeautifulSoup(template_content, 'html.parser')
        
        # Find the modal element
        modal = soup.find('div', {'id': 'customizeModal'})
        
        # Verify the modal exists
        self.assertIsNotNone(modal, "Modal with id 'customizeModal' should exist")
        
        # Verify the modal has the correct classes
        classes = modal.get('class', [])
        self.assertIn('modal', classes, "Modal should have 'modal' class")
        self.assertIn('modal-blur', classes, "Modal should have 'modal-blur' class for backdrop effect")
        self.assertIn('modal-lg', classes, "Modal should have 'modal-lg' class for size")
        self.assertIn('fade', classes, "Modal should have 'fade' class for animation")
        
    def test_modal_has_correct_structure(self):
        """Test that the modal has the correct Bootstrap structure for centering."""
        # Read the template file
        template_path = os.path.join(os.path.dirname(__file__), '../templates/email_template_customization.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Parse the HTML content
        soup = BeautifulSoup(template_content, 'html.parser')
        
        # Find the modal dialog
        modal_dialog = soup.find('div', class_='modal-dialog')
        
        # Verify the modal dialog exists and has centering class
        self.assertIsNotNone(modal_dialog, "Modal dialog should exist")
        classes = modal_dialog.get('class', [])
        self.assertIn('modal-dialog-centered', classes, "Modal dialog should have centering class")
        # The modal-lg class should be on the outer modal, not the dialog
        # Modal dialog should have modal-dialog and modal-dialog-centered
        
    def test_modal_has_proper_attributes(self):
        """Test that the modal has proper Bootstrap attributes."""
        # Read the template file
        template_path = os.path.join(os.path.dirname(__file__), '../templates/email_template_customization.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Parse the HTML content
        soup = BeautifulSoup(template_content, 'html.parser')
        
        # Find the modal element
        modal = soup.find('div', {'id': 'customizeModal'})
        
        # Verify proper Bootstrap modal attributes
        self.assertEqual(modal.get('tabindex'), '-1', "Modal should have tabindex='-1'")
        self.assertEqual(modal.get('aria-labelledby'), 'customizeModalLabel', "Modal should have proper aria-labelledby")
        self.assertEqual(modal.get('aria-hidden'), 'true', "Modal should have aria-hidden='true'")

if __name__ == '__main__':
    unittest.main()