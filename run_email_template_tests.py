#!/usr/bin/env python3
"""
Test runner for email template customization system.

Usage:
    python run_email_template_tests.py
    
This script runs the comprehensive unit tests for the newly implemented
email template customization system.
"""

import sys
import os
import subprocess

def run_tests():
    """Run the email template tests"""
    print("🧪 Running Email Template Customization Tests")
    print("=" * 50)
    
    # Change to the app directory if not already there
    if not os.path.basename(os.getcwd()) == 'app':
        if os.path.exists('app'):
            os.chdir('app')
        elif os.path.exists('../app'):
            os.chdir('../app')
    
    # Activate virtual environment and run tests
    try:
        # Try to run with virtual environment
        result = subprocess.run([
            'bash', '-c', 
            'source venv/bin/activate && python -m unittest test.test_email_templates -v'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode == 0:
            print("\n✅ All email template tests passed!")
            return True
        else:
            print("\n❌ Some tests failed.")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        print("\nTrying without virtual environment...")
        
        # Fallback: try without virtual environment
        try:
            result = subprocess.run([
                'python', '-m', 'unittest', 'test.test_email_templates', '-v'
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            if result.returncode == 0:
                print("\n✅ All email template tests passed!")
                return True
            else:
                print("\n❌ Some tests failed.")
                return False
                
        except Exception as e2:
            print(f"❌ Error running tests without venv: {e2}")
            return False

def run_specific_test(test_name):
    """Run a specific test method"""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            'bash', '-c', 
            f'source venv/bin/activate && python -m unittest test.test_email_templates.TestEmailTemplateCustomization.{test_name} -v'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)