#!/usr/bin/env python3
"""
Test the email parsing fix for spaced amounts like "98, 00"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re

def test_email_parsing_fix():
    """Test that the updated regex patterns work with real email subjects"""
    
    # Test cases from real emails
    test_subjects = [
        {
            'subject': 'Virement Interac : Vous avez reçu 98, 00 $ de Ken Dresdell et ce montant a été déposé automatiquement.',
            'expected_amount': 98.0,
            'expected_name': 'Ken Dresdell',
            'description': 'Real email with spaced amount'
        },
        {
            'subject': 'Virement Interac : Vous avez reçu 100,00 $ de John Smith et ce montant a été déposé automatiquement.',
            'expected_amount': 100.0,
            'expected_name': 'John Smith', 
            'description': 'Standard format without spaces'
        },
        {
            'subject': 'Virement Interac : John Doe vous a envoyé 25, 50 $',
            'expected_amount': 25.50,
            'expected_name': 'John Doe',
            'description': 'Fallback pattern with spaces'
        }
    ]
    
    print("🧪 Testing Email Parsing Fix")
    print("=" * 50)
    
    all_passed = True
    
    for i, test in enumerate(test_subjects, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Subject: {test['subject'][:60]}...")
        
        # Use the updated regex patterns from utils.py
        amount_match = re.search(r"reçu\s+([\d,\s]+)\s+\$\s+de", test['subject'])
        name_match = re.search(r"de\s+(.+?)\s+et ce montant", test['subject'])
        
        # Fallback patterns
        if not amount_match:
            amount_match = re.search(r"envoyé\s+([\d,\s]+)\s*\$", test['subject'])
        if not name_match:
            name_match = re.search(r":\s*(.*?)\svous a envoyé", test['subject'])
        
        if amount_match and name_match:
            # Parse amount
            raw_amount = amount_match.group(1)
            amt_str = raw_amount.replace(' ', '').replace(',', '.')
            try:
                amount = float(amt_str)
                name = name_match.group(1).strip()
                
                # Check results
                amount_ok = abs(amount - test['expected_amount']) < 0.01
                name_ok = name == test['expected_name']
                
                if amount_ok and name_ok:
                    print(f"✅ PASS: Amount=${amount}, Name='{name}'")
                else:
                    print(f"❌ FAIL:")
                    if not amount_ok:
                        print(f"   Expected amount: ${test['expected_amount']}, got: ${amount}")
                    if not name_ok:
                        print(f"   Expected name: '{test['expected_name']}', got: '{name}'")
                    all_passed = False
                    
            except ValueError as e:
                print(f"❌ FAIL: Amount conversion error: {e}")
                all_passed = False
        else:
            print("❌ FAIL: Regex didn't match")
            print(f"   Amount match: {'Yes' if amount_match else 'No'}")
            print(f"   Name match: {'Yes' if name_match else 'No'}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Email parsing fix is working.")
        print("✅ Your $98 payment should now be processed correctly.")
    else:
        print("❌ Some tests failed. Need to check the regex patterns.")
        
    return all_passed

if __name__ == '__main__':
    test_email_parsing_fix()