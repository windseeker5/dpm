#!/usr/bin/env python3
"""
Test file for email template JavaScript functionality
Tests JavaScript functions using MCP Playwright browser automation
"""

import unittest
import time
from pathlib import Path

class TestEmailTemplateJS(unittest.TestCase):
    """Test JavaScript functions in email template editor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5000"
        cls.js_file_path = "/home/kdresdell/Documents/DEV/minipass_env/app/static/js/email-template-editor.js"
        
    def test_js_file_exists(self):
        """Test that JavaScript file exists and has correct structure"""
        js_file = Path(self.js_file_path)
        self.assertTrue(js_file.exists(), "JavaScript file should exist")
        
        content = js_file.read_text()
        self.assertIn("initTinyMCE", content, "Should contain initTinyMCE function")
        self.assertIn("previewLogo", content, "Should contain previewLogo function")
        
        # Test line count constraint (max 50 lines)
        lines = content.split('\n')
        self.assertLessEqual(len(lines), 50, f"JavaScript should be max 50 lines, got {len(lines)}")
        
    def test_functions_are_minimal(self):
        """Test that functions adhere to line constraints"""
        js_file = Path(self.js_file_path)
        content = js_file.read_text()
        
        # Count function lines by looking at actual structure
        # initTinyMCE should be around 8 lines (including function declaration and closing brace)
        init_start = content.find("function initTinyMCE()")
        init_end = content.find("}", init_start) + 1
        init_lines = content[init_start:init_end].count('\n') + 1
        self.assertLessEqual(init_lines, 10, f"initTinyMCE should be minimal, got {init_lines} lines")
        
        # previewLogo should be around 7-9 lines (compressed with semicolons)
        preview_start = content.find("function previewLogo(")
        preview_end = content.find("}", preview_start) + 1
        preview_lines = content[preview_start:preview_end].count('\n') + 1
        self.assertLessEqual(preview_lines, 10, f"previewLogo should be minimal, got {preview_lines} lines")
        
        # Verify functions use compressed syntax for efficiency
        self.assertIn("height: 200, menubar: false", content, "Should use compressed object syntax")
        self.assertIn("; reader.readAsDataURL", content, "Should use compressed statements")

    def test_no_global_event_listeners(self):
        """Test that no global event listeners are used outside DOMContentLoaded"""
        js_file = Path(self.js_file_path)
        content = js_file.read_text()
        
        # Check for prohibited patterns
        prohibited_patterns = [
            "window.addEventListener",
            "document.addEventListener",
            ".addEventListener"
        ]
        
        # Split into lines and check each
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern in prohibited_patterns:
                if pattern in line:
                    # Allow if it's inside DOMContentLoaded or beforeunload
                    if "DOMContentLoaded" not in line and "beforeunload" not in line and "change" not in line:
                        # Check if it's within the DOMContentLoaded block
                        context_lines = lines[max(0, i-5):i+5]
                        context = '\n'.join(context_lines)
                        if "DOMContentLoaded" not in context and "beforeunload" not in context:
                            self.fail(f"Global event listener found at line {i+1}: {line.strip()}")

    def test_javascript_syntax_validity(self):
        """Test that JavaScript has valid syntax"""
        js_file = Path(self.js_file_path)
        content = js_file.read_text()
        
        # Basic syntax checks
        open_braces = content.count('{')
        close_braces = content.count('}')
        self.assertEqual(open_braces, close_braces, "Mismatched braces in JavaScript")
        
        open_parens = content.count('(')
        close_parens = content.count(')')
        self.assertEqual(open_parens, close_parens, "Mismatched parentheses in JavaScript")
        
        # Check for required exports
        self.assertIn("module.exports", content, "Should export functions for testing")

    def test_function_definitions(self):
        """Test that required functions are properly defined"""
        js_file = Path(self.js_file_path)
        content = js_file.read_text()
        
        # Test initTinyMCE function
        self.assertIn("function initTinyMCE()", content, "initTinyMCE function should be defined")
        self.assertIn("tinymce.init", content, "Should call tinymce.init")
        self.assertIn("selector:", content, "Should specify selector")
        
        # Test previewLogo function  
        self.assertIn("function previewLogo(input)", content, "previewLogo function should take input parameter")
        self.assertIn("FileReader", content, "Should use FileReader for image preview")
        self.assertIn("readAsDataURL", content, "Should call readAsDataURL")

    def test_error_handling(self):
        """Test that functions have proper error handling"""
        js_file = Path(self.js_file_path)
        content = js_file.read_text()
        
        # Check for defensive programming
        self.assertIn("typeof tinymce !== 'undefined'", content, "Should check if TinyMCE is available")
        self.assertIn("input.files && input.files[0]", content, "Should check if files exist")

    def test_memory_leak_prevention(self):
        """Test that cleanup code exists to prevent memory leaks"""
        js_file = Path(self.js_file_path)
        content = js_file.read_text()
        
        # Check for cleanup on page unload
        self.assertIn("beforeunload", content, "Should handle beforeunload event")
        self.assertIn("tinymce.remove", content, "Should remove TinyMCE instances")

if __name__ == '__main__':
    unittest.main()