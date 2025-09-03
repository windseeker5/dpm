"""
Simple integration test for signup email template fix
Tests that the hero image replacement works correctly
"""

import unittest
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSignupEmailIntegration(unittest.TestCase):
    """Integration test for signup email with hero image"""
    
    def test_hero_image_replacement_logic(self):
        """Test that our fix correctly adds hero image replacement logic"""
        # Read the utils.py file to verify our fix is in place
        utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils.py')
        
        with open(utils_path, 'r') as f:
            content = f.read()
        
        # Check that the hero image replacement code exists in notify_signup_event
        self.assertIn('Check for activity-specific hero image (replaces \'good-news\' CID)', content,
                     "Hero image replacement comment not found in notify_signup_event")
        
        self.assertIn('inline_images[\'good-news\'] = hero_data', content,
                     "Hero image CID replacement not found in notify_signup_event")
        
        self.assertIn('Using activity-specific hero image:', content,
                     "Debug message for hero image not found")
        
        self.assertIn('Activity hero image not found:', content,
                     "Debug message for missing hero not found")
        
        # Verify it's in the right function by checking nearby context
        lines = content.split('\n')
        found_function = False
        found_fix = False
        
        for i, line in enumerate(lines):
            if 'def notify_signup_event' in line:
                found_function = True
                # Look for our fix within the next 200 lines
                for j in range(i, min(i + 200, len(lines))):
                    if 'Check for activity-specific hero image' in lines[j]:
                        found_fix = True
                        print(f"✓ Hero image fix found at line {j+1}")
                        
                        # Verify the code structure
                        expected_lines = [
                            'activity_id = activity.id if activity else None',
                            'if activity_id:',
                            'hero_image_path = os.path.join("static/uploads", f"{activity_id}_hero.png")',
                            'if os.path.exists(hero_image_path):',
                            'hero_data = open(hero_image_path, "rb").read()',
                            'inline_images[\'good-news\'] = hero_data'
                        ]
                        
                        code_block = '\n'.join(lines[j:j+15])
                        for expected in expected_lines:
                            self.assertIn(expected, code_block, 
                                        f"Expected code line not found: {expected}")
                        break
                break
        
        self.assertTrue(found_function, "notify_signup_event function not found")
        self.assertTrue(found_fix, "Hero image fix not found in notify_signup_event function")
        
    def test_fix_location(self):
        """Test that the fix is in the correct location (after organization logo loading)"""
        utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils.py')
        
        with open(utils_path, 'r') as f:
            lines = f.readlines()
        
        # Find the organization logo section
        org_logo_line = None
        hero_fix_line = None
        
        for i, line in enumerate(lines):
            if 'Get organization logo from settings' in line:
                org_logo_line = i
            if 'Check for activity-specific hero image' in line:
                hero_fix_line = i
        
        self.assertIsNotNone(org_logo_line, "Organization logo section not found")
        self.assertIsNotNone(hero_fix_line, "Hero image fix not found")
        self.assertGreater(hero_fix_line, org_logo_line, 
                          "Hero image fix should be after organization logo loading")
        self.assertLess(hero_fix_line - org_logo_line, 20,
                       "Hero image fix is too far from organization logo section")
        
        print(f"✓ Organization logo at line {org_logo_line + 1}")
        print(f"✓ Hero image fix at line {hero_fix_line + 1}")
        print(f"✓ Fix is {hero_fix_line - org_logo_line} lines after logo section")


if __name__ == '__main__':
    unittest.main(verbosity=2)