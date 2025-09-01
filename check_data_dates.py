#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import Passport, Income, db
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

def check_data_distribution():
    """Check when our passport and income data was created"""
    with app.app_context():
        # Check passport creation dates
        print("=== PASSPORT CREATION DATES ===")
        passports = db.session.query(
            func.date(Passport.created_dt).label('date'),
            func.count().label('count'),
            func.sum(Passport.sold_amt).label('revenue')
        ).group_by(func.date(Passport.created_dt)).order_by(func.date(Passport.created_dt).desc()).limit(10).all()
        
        for p in passports:
            print(f"Date: {p.date}, Count: {p.count}, Revenue: ${p.revenue or 0}")
        
        # Check income dates
        print("\n=== INCOME DATES ===")
        incomes = db.session.query(
            func.date(Income.date).label('date'),
            func.count().label('count'),
            func.sum(Income.amount).label('revenue')
        ).group_by(func.date(Income.date)).order_by(func.date(Income.date).desc()).limit(10).all()
        
        for i in incomes:
            print(f"Date: {i.date}, Count: {i.count}, Revenue: ${i.revenue or 0}")
        
        # Check current time ranges
        now = datetime.now(timezone.utc)
        print(f"\n=== TIME ANALYSIS ===")
        print(f"Current time (UTC): {now}")
        print(f"7d ago: {now - timedelta(days=7)}")
        print(f"14d ago (prev 7d start): {now - timedelta(days=14)}")
        print(f"30d ago: {now - timedelta(days=30)}")
        print(f"60d ago (prev 30d start): {now - timedelta(days=60)}")

if __name__ == "__main__":
    check_data_distribution()