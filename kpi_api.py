# KPI API for Activity Dashboard
# This file contains the corrected KPI API implementation

from flask import request, jsonify, session
from datetime import datetime, timezone, timedelta

# This can be imported into app.py and registered as a route
def register_kpi_routes(app):
    """Register the corrected KPI API routes with the Flask app"""
    
    @app.route("/api/activity-kpis/<int:activity_id>")
    def get_activity_kpis_corrected(activity_id):
        return get_activity_kpis_implementation(activity_id)

def get_activity_kpis_implementation(activity_id):
    """API endpoint to get KPI data for different time periods
    
    Fixes:
    1. Ensures exactly N data points for N-day periods
    2. Proper encoding for percentage values
    3. Clean numeric data without special characters
    4. Consistent date range calculations
    """
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Get time period from query parameter (default to 7 days)
    period_days = request.args.get('period', '7')
    try:
        period_days = int(period_days)
        if period_days not in [7, 30, 90]:
            period_days = 7
    except ValueError:
        period_days = 7

    from models import Activity, Passport, db

    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404

    # Calculate date range
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=period_days)
    
    # Get all passports for this activity
    all_passports = Passport.query.filter_by(activity_id=activity_id).all()
    
    # Helper function to safely compare dates
    def is_recent(dt, cutoff_date):
        if not dt:
            return False
        # Make timezone-naive datetime timezone-aware if needed
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff_date
    
    # Revenue calculations for the time period
    total_revenue = sum(p.sold_amt for p in all_passports if p.paid)
    period_revenue = sum(p.sold_amt for p in all_passports if p.paid and is_recent(p.created_dt, cutoff_date))
    
    # Calculate percentage change using proper period-over-period comparison
    # Get previous period data for accurate percentage calculation
    previous_period_start = cutoff_date - timedelta(days=period_days)
    previous_period_end = cutoff_date
    
    previous_revenue_passports = Passport.query.filter_by(activity_id=activity_id, paid=True).filter(
        db.or_(
            db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= previous_period_start, Passport.paid_date < previous_period_end),
            db.and_(Passport.paid_date.is_(None), Passport.created_dt >= previous_period_start, Passport.created_dt < previous_period_end)
        )
    ).all()
    
    previous_revenue = sum(p.sold_amt for p in previous_revenue_passports if p.sold_amt is not None)
    
    # Calculate percentage change: (current - previous) / previous * 100
    # Ensure clean numeric output without encoding issues
    revenue_change = 0.0
    if previous_revenue > 0:
        raw_change = ((period_revenue - previous_revenue) / previous_revenue) * 100
        revenue_change = float(round(raw_change, 1))  # Explicit float conversion
    elif period_revenue > 0:
        revenue_change = 100.0  # 100% increase from 0
    
    # Active users for the time period
    active_users_total = len([p for p in all_passports if p.paid and p.uses_remaining > 0])
    active_users_period = len([p for p in all_passports if is_recent(p.created_dt, cutoff_date)])
    
    # Calculate active users percentage change - timezone-safe
    previous_active_users = 0
    for p in all_passports:
        if p.created_dt and p.uses_remaining > 0:
            p_dt = p.created_dt
            if p_dt.tzinfo is None:
                p_dt = p_dt.replace(tzinfo=timezone.utc)
            if previous_period_start <= p_dt < previous_period_end:
                previous_active_users += 1
    
    active_users_change = 0.0
    if previous_active_users > 0:
        raw_change = ((active_users_period - previous_active_users) / previous_active_users) * 100
        active_users_change = float(round(raw_change, 1))  # Explicit float conversion
    elif active_users_period > 0:
        active_users_change = 100.0
    
    # Unpaid passport statistics
    unpaid_passports = [p for p in all_passports if not p.paid]
    unpaid_count = len(unpaid_passports)
    overdue_threshold = now - timedelta(days=3)  # Consider 3+ days as overdue
    overdue_count = len([p for p in unpaid_passports if p.created_dt and not is_recent(p.created_dt, overdue_threshold)])
    
    # Activity profit calculation
    try:
        activity_expenses = sum(e.amount for e in activity.expenses) if hasattr(activity, 'expenses') else 0
        activity_income = sum(i.amount for i in activity.incomes) if hasattr(activity, 'incomes') else 0
        total_income = total_revenue + activity_income
        profit = total_income - activity_expenses
        profit_margin = (profit / total_income * 100) if total_income > 0 else 0
    except:
        profit = total_revenue
        profit_margin = 100
    
    # Build daily trend data for charts
    # Fixed to ensure exactly N data points for N-day periods
    def build_revenue_trend(days):
        """Generate exactly 'days' number of data points for the chart
        
        For 7 days: returns 7 data points (day 6, day 5, ..., day 0)
        For 30 days: returns 30 data points 
        For 90 days: returns 90 data points
        """
        trend = []
        
        # Generate exactly 'days' number of data points
        for i in range(days):
            # Calculate the date range for this specific day
            # i=0 is today, i=1 is yesterday, etc.
            start = now - timedelta(days=i+1)
            end = now - timedelta(days=i)
            
            # Query passports for this specific day
            daily_passports = Passport.query.filter_by(activity_id=activity_id, paid=True).filter(
                db.or_(
                    db.and_(Passport.paid_date.isnot(None), Passport.paid_date >= start, Passport.paid_date < end),
                    db.and_(Passport.paid_date.is_(None), Passport.created_dt >= start, Passport.created_dt < end)
                )
            ).all()
            
            # Calculate revenue for this day with clean numeric output
            daily_revenue = sum(float(p.sold_amt) for p in daily_passports if p.sold_amt is not None)
            trend.append(float(round(daily_revenue, 2)))  # Explicit float conversion
        
        # Reverse to get chronological order (oldest to newest)
        trend.reverse()
        
        # Validate we have exactly the right number of data points
        assert len(trend) == days, f"Expected {days} data points, got {len(trend)}"
        
        return trend
    
    # Build active users trend data
    def build_active_users_trend(days):
        """Generate active users trend data with exactly 'days' data points"""
        trend = []
        
        for i in range(days):
            start = now - timedelta(days=i+1) 
            end = now - timedelta(days=i)
            
            # Count active users created on this specific day
            # Use timezone-safe comparison
            daily_active_users = 0
            for p in all_passports:
                if (p.created_dt and p.paid and p.uses_remaining > 0):
                    # Make timezone-aware comparison
                    p_dt = p.created_dt
                    if p_dt.tzinfo is None:
                        p_dt = p_dt.replace(tzinfo=timezone.utc)
                    if start <= p_dt < end:
                        daily_active_users += 1
            
            trend.append(int(daily_active_users))  # Ensure integer
        
        trend.reverse()  # Chronological order
        
        # Pad with zeros if we don't have enough data
        while len(trend) < days:
            trend.insert(0, 0)
            
        return trend[:days]  # Ensure exactly 'days' points
    
    # Build unpaid passports trend data
    def build_unpaid_trend(days):
        """Generate unpaid passports trend with exactly 'days' data points"""
        trend = []
        
        for i in range(days):
            start = now - timedelta(days=i+1)
            end = now - timedelta(days=i)
            
            # Count unpaid passports created on this day
            daily_unpaid = 0
            for p in all_passports:
                if not p.paid and p.created_dt:
                    # Make timezone-aware comparison
                    p_dt = p.created_dt
                    if p_dt.tzinfo is None:
                        p_dt = p_dt.replace(tzinfo=timezone.utc)
                    if start <= p_dt < end:
                        daily_unpaid += 1
            
            trend.append(int(daily_unpaid))
        
        trend.reverse()
        
        # Pad with zeros if needed
        while len(trend) < days:
            trend.insert(0, 0)
            
        return trend[:days]
    
    # Generate trend data for all KPIs
    revenue_trend_data = build_revenue_trend(period_days)
    active_users_trend_data = build_active_users_trend(period_days)
    unpaid_trend_data = build_unpaid_trend(period_days)
    
    # Validate trend data lengths
    assert len(revenue_trend_data) == period_days, f"Revenue trend has {len(revenue_trend_data)} points, expected {period_days}"
    assert len(active_users_trend_data) == period_days, f"Active users trend has {len(active_users_trend_data)} points, expected {period_days}"
    assert len(unpaid_trend_data) == period_days, f"Unpaid trend has {len(unpaid_trend_data)} points, expected {period_days}"
    
    # Build KPI response with clean, properly encoded data
    kpi_data = {
        'revenue': {
            'total': float(total_revenue),
            'period_value': float(period_revenue),
            'trend': 'up' if revenue_change > 0 else ('down' if revenue_change < 0 else 'stable'),
            'percentage': revenue_change,  # Already converted to clean float
            'trend_data': revenue_trend_data  # Exactly period_days data points
        },
        'active_users': {
            'total': int(active_users_total),
            'period_value': int(active_users_period), 
            'trend': 'up' if active_users_change > 0 else ('down' if active_users_change < 0 else 'stable'),
            'percentage': active_users_change,  # Already converted to clean float
            'trend_data': active_users_trend_data  # Exactly period_days data points
        },
        'unpaid_passports': {
            'total': int(unpaid_count),
            'overdue': int(overdue_count),
            'trend': 'down' if overdue_count == 0 else 'up',
            'percentage': float(overdue_count),
            'trend_data': unpaid_trend_data  # Exactly period_days data points
        },
        'profit': {
            'total': float(profit),
            'margin': float(round(profit_margin, 1)),
            'trend': 'up' if profit > 0 else 'stable',
            'percentage': float(round(profit_margin, 1)),
            'trend_data': revenue_trend_data  # Use revenue trend as proxy
        }
    }
    
    # Final response with debug information
    response_data = {
        'success': True,
        'period_days': int(period_days),
        'kpi_data': kpi_data,
        'debug': {
            'revenue_trend_length': len(revenue_trend_data),
            'active_users_trend_length': len(active_users_trend_data),
            'unpaid_trend_length': len(unpaid_trend_data),
            'data_validation': 'passed'
        }
    }
    
    return jsonify(response_data)