#!/usr/bin/env python3
"""
Template Validation Test for Activity Dashboard
Tests to verify that the template file is valid after removing checkbox functionality.
"""

import unittest
import os
import re

class TestTemplateValidation(unittest.TestCase):
    """Test the activity dashboard template file directly."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.template_path = "/home/kdresdell/Documents/DEV/minipass_env/app/templates/activity_dashboard.html"
        
        # Read template content
        with open(cls.template_path, 'r', encoding='utf-8') as f:
            cls.template_content = f.read()
    
    def test_template_file_exists(self):
        """Test that the template file exists and is readable."""
        self.assertTrue(os.path.exists(self.template_path), "Template file should exist")
        self.assertGreater(len(self.template_content), 1000, "Template should have substantial content")
        print("✅ Template file exists and has content")
    
    def test_no_checkbox_html_elements(self):
        """Test that no checkbox HTML elements remain."""
        # Check for checkbox input elements
        checkbox_inputs = re.findall(r'<input[^>]*type=["\']checkbox["\'][^>]*>', self.template_content)
        self.assertEqual(len(checkbox_inputs), 0, 
                        f"Found {len(checkbox_inputs)} checkbox inputs: {checkbox_inputs[:3]}")
        
        # Check for checkbox classes
        checkbox_classes = re.findall(r'class=["\'][^"\']*checkbox[^"\']*["\']', self.template_content)
        self.assertEqual(len(checkbox_classes), 0, 
                        f"Found {len(checkbox_classes)} checkbox classes: {checkbox_classes[:3]}")
        
        print("✅ No checkbox HTML elements found")
    
    def test_no_bulk_actions_containers(self):
        """Test that no bulk actions container elements remain."""
        # Check for bulk actions containers
        bulk_containers = re.findall(r'bulk-actions-container', self.template_content)
        self.assertEqual(len(bulk_containers), 0, 
                        f"Found {len(bulk_containers)} bulk-actions-container references")
        
        # Check for bulk actions cards
        bulk_cards = re.findall(r'bulk-actions-card', self.template_content)
        self.assertEqual(len(bulk_cards), 0, 
                        f"Found {len(bulk_cards)} bulk-actions-card references")
        
        # Check for bulkActions ID
        bulk_actions_id = re.findall(r'id=["\']bulkActions["\']', self.template_content)
        self.assertEqual(len(bulk_actions_id), 0, 
                        f"Found {len(bulk_actions_id)} bulkActions ID references")
        
        print("✅ No bulk actions containers found")
    
    def test_no_select_all_checkboxes(self):
        """Test that no select all checkbox elements remain."""
        select_all = re.findall(r'id=["\']selectAll["\']', self.template_content)
        self.assertEqual(len(select_all), 0, 
                        f"Found {len(select_all)} selectAll ID references")
        
        print("✅ No select all checkboxes found")
    
    def test_no_passport_signup_checkboxes(self):
        """Test that no passport or signup checkbox classes remain."""
        passport_checkboxes = re.findall(r'passport-checkbox', self.template_content)
        self.assertEqual(len(passport_checkboxes), 0, 
                        f"Found {len(passport_checkboxes)} passport-checkbox references")
        
        signup_checkboxes = re.findall(r'signup-checkbox', self.template_content)
        self.assertEqual(len(signup_checkboxes), 0, 
                        f"Found {len(signup_checkboxes)} signup-checkbox references")
        
        print("✅ No passport/signup checkbox classes found")
    
    def test_no_bulk_delete_modal(self):
        """Test that the bulk delete modal is removed."""
        bulk_modal = re.findall(r'id=["\']bulkDeleteModal["\']', self.template_content)
        self.assertEqual(len(bulk_modal), 0, 
                        f"Found {len(bulk_modal)} bulkDeleteModal ID references")
        
        print("✅ No bulk delete modal found")
    
    def test_no_bulk_actions_javascript(self):
        """Test that bulk actions JavaScript functions are removed."""
        # Check for initializePassportBulkSelection function
        bulk_init = re.findall(r'function\s+initializePassportBulkSelection', self.template_content)
        self.assertEqual(len(bulk_init), 0, 
                        f"Found {len(bulk_init)} initializePassportBulkSelection function references")
        
        # Check for showBulkDeleteModal function
        bulk_delete_fn = re.findall(r'function\s+showBulkDeleteModal', self.template_content)
        self.assertEqual(len(bulk_delete_fn), 0, 
                        f"Found {len(bulk_delete_fn)} showBulkDeleteModal function references")
        
        # Check for updateBulkActions function
        update_bulk = re.findall(r'function\s+updateBulkActions', self.template_content)
        self.assertEqual(len(update_bulk), 0, 
                        f"Found {len(update_bulk)} updateBulkActions function references")
        
        print("✅ No bulk actions JavaScript functions found")
    
    def test_no_bulk_actions_css(self):
        """Test that bulk actions CSS is removed."""
        # Check for bulk actions CSS classes
        css_patterns = [
            r'\.bulk-actions-container',
            r'\.bulk-actions-card',
            r'\.bulk-actions-count',
            r'\.bulk-actions-buttons',
        ]
        
        found_css = []
        for pattern in css_patterns:
            matches = re.findall(pattern, self.template_content)
            if matches:
                found_css.extend(matches)
        
        self.assertEqual(len(found_css), 0, 
                        f"Found {len(found_css)} bulk actions CSS references: {found_css[:5]}")
        
        print("✅ No bulk actions CSS found")
    
    def test_individual_actions_preserved(self):
        """Test that individual Actions dropdowns are preserved."""
        # Check for dropdown elements
        dropdowns = re.findall(r'dropdown-toggle', self.template_content)
        self.assertGreater(len(dropdowns), 0, "Should have dropdown-toggle elements for individual actions")
        
        # Check for Actions text
        actions_text = re.findall(r'>Actions<', self.template_content)
        self.assertGreater(len(actions_text), 0, "Should have Actions text in dropdowns")
        
        # Check for dropdown items
        dropdown_items = re.findall(r'dropdown-item', self.template_content)
        self.assertGreater(len(dropdown_items), 0, "Should have dropdown-item elements")
        
        print(f"✅ Individual actions preserved ({len(dropdowns)} dropdowns, {len(dropdown_items)} items)")
    
    def test_tables_structure_preserved(self):
        """Test that table structures are preserved."""
        # Check for table elements
        tables = re.findall(r'<table[^>]*class=["\'][^"\']*table', self.template_content)
        self.assertGreater(len(tables), 0, "Should have table elements")
        
        # Check for table headers
        theads = re.findall(r'<thead>', self.template_content)
        self.assertGreater(len(theads), 0, "Should have table headers")
        
        # Check for table bodies
        tbodies = re.findall(r'<tbody>', self.template_content)
        self.assertGreater(len(tbodies), 0, "Should have table bodies")
        
        print(f"✅ Table structure preserved ({len(tables)} tables)")
    
    def test_filter_buttons_preserved(self):
        """Test that filter buttons are preserved."""
        # Check for filter buttons
        filter_buttons = re.findall(r'github-filter-btn', self.template_content)
        self.assertGreater(len(filter_buttons), 0, "Should have filter buttons")
        
        # Check for filter functions
        filter_functions = re.findall(r'filterPassports|filterSignups', self.template_content)
        self.assertGreater(len(filter_functions), 0, "Should have filter functions")
        
        print(f"✅ Filter functionality preserved ({len(filter_buttons)} filter buttons)")
    
    def test_no_orphaned_form_references(self):
        """Test that there are no orphaned references to removed bulk forms."""
        # Check for form="bulkForm" references
        bulk_form_refs = re.findall(r'form=["\']bulkForm["\']', self.template_content)
        self.assertEqual(len(bulk_form_refs), 0, 
                        f"Found {len(bulk_form_refs)} orphaned bulkForm references")
        
        print("✅ No orphaned form references found")
    
    def test_template_syntax_valid(self):
        """Test that the template has valid HTML/Jinja2 syntax."""
        # Basic syntax checks
        open_tags = len(re.findall(r'<(?!/)(?!\?)[^>]*>', self.template_content))
        close_tags = len(re.findall(r'</[^>]*>', self.template_content))
        
        # Allow for some difference due to self-closing tags
        tag_difference = abs(open_tags - close_tags)
        self.assertLess(tag_difference, 50, 
                       f"Large tag mismatch: {open_tags} open, {close_tags} close")
        
        # Check for obvious syntax errors
        syntax_errors = []
        
        # Check for unmatched quotes in attributes
        unmatched_quotes = re.findall(r'=["\'][^"\']*$', self.template_content, re.MULTILINE)
        if unmatched_quotes:
            syntax_errors.append(f"Possible unmatched quotes: {len(unmatched_quotes)}")
        
        # Check for unclosed Jinja2 blocks
        jinja_open = len(re.findall(r'\{\%\s*\w+', self.template_content))
        jinja_close = len(re.findall(r'\{\%\s*end\w+', self.template_content))
        if abs(jinja_open - jinja_close) > 5:  # Allow some tolerance
            syntax_errors.append(f"Jinja2 block mismatch: {jinja_open} open, {jinja_close} close")
        
        self.assertEqual(len(syntax_errors), 0, f"Syntax errors found: {syntax_errors}")
        
        print("✅ Template syntax appears valid")


def run_tests():
    """Run all template validation tests."""
    print("🔍 Running Template Validation Tests")
    print("=" * 50)
    
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()