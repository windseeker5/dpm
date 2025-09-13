#!/usr/bin/env python3
"""
Test script to verify payment matching fixes work correctly.
This simulates the payment matching logic without actually processing emails.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Passport, User, Activity
import unicodedata
from rapidfuzz import fuzz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/minipass.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def normalize_name(text):
    """Remove accents and normalize text for better matching"""
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower().strip()

def test_payment_matching():
    """Test the payment matching logic with real data"""
    with app.app_context():
        print("🧪 TESTING PAYMENT MATCHING FIXES")
        print("=" * 50)
        
        # Test cases based on real payment logs
        test_cases = [
            {
                "payment_name": "STEVEN BELANGER",
                "payment_amount": 320.0,
                "expected_match": "Steven Bélanger",  # With accent
                "description": "Steven Belanger accent test"
            },
            {
                "payment_name": "Jean-Francois Gagne", 
                "payment_amount": 50.0,
                "expected_match": "Jean-Francois Gagne",
                "description": "Jean-Francois exact match test"
            }
        ]
        
        # Get unpaid passports
        unpaid_passports = Passport.query.filter_by(paid=False).all()
        print(f"📋 Found {len(unpaid_passports)} unpaid passports")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 TEST CASE {i}: {test_case['description']}")
            print(f"   Payment: {test_case['payment_name']} - ${test_case['payment_amount']}")
            
            payment_name = test_case['payment_name']
            payment_amount = test_case['payment_amount']
            
            # Normalize payment name
            normalized_payment_name = normalize_name(payment_name)
            print(f"   Normalized: '{payment_name}' → '{normalized_payment_name}'")
            
            # Find matches
            exact_matches = []
            fuzzy_matches = []
            threshold = 85
            
            for p in unpaid_passports:
                if not p.user:
                    continue
                
                normalized_passport_name = normalize_name(p.user.name)
                score = fuzz.ratio(normalized_payment_name, normalized_passport_name)
                
                if score >= 95:
                    exact_matches.append((p, score))
                elif score >= threshold:
                    fuzzy_matches.append((p, score))
            
            candidates = exact_matches if exact_matches else fuzzy_matches
            candidate_type = "exact" if exact_matches else "fuzzy"
            
            print(f"   Found {len(exact_matches)} exact matches, {len(fuzzy_matches)} fuzzy matches")
            print(f"   Using {candidate_type} matches")
            
            # Find amount matches
            amount_matches = []
            for p, score in candidates:
                print(f"      Candidate: {p.user.name} - ${p.sold_amt} (Score: {score}%)")
                if abs(p.sold_amt - payment_amount) < 1:
                    amount_matches.append((p, score))
                    print(f"         ✅ Amount match!")
                else:
                    print(f"         ❌ Amount mismatch (diff: ${abs(p.sold_amt - payment_amount)})")
            
            # Select best match
            if amount_matches:
                amount_matches.sort(key=lambda x: (-x[1], x[0].created_dt))
                best_passport = amount_matches[0][0]
                best_score = amount_matches[0][1]
                print(f"   🎯 RESULT: MATCH - {best_passport.user.name} (Passport #{best_passport.id})")
                print(f"      Score: {best_score}%, Amount: ${best_passport.sold_amt}")
            else:
                print(f"   ❌ RESULT: NO MATCH")
                if candidates:
                    print(f"      Reason: Name matched but amount mismatch")
                else:
                    print(f"      Reason: No name matches above {threshold}% threshold")
        
        print(f"\n🏁 TEST COMPLETE")

if __name__ == "__main__":
    test_payment_matching()