@app.route("/api/activity-kpis/<int:activity_id>")
def get_activity_kpis(activity_id):
    """API endpoint to get KPI data for different time periods"""
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

    from models import Activity, Passport
    from datetime import datetime, timezone, timedelta

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
    
    # Calculate percentage change (mock for now, could implement proper calculation)
    revenue_change = (period_revenue / total_revenue * 100) if total_revenue > 0 else 0
    
    # Active users for the time period
    active_users_total = len([p for p in all_passports if p.paid and p.uses_remaining > 0])
    active_users_period = len([p for p in all_passports if is_recent(p.created_dt, cutoff_date)])
    
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
    
    # Build KPI response
    kpi_data = {
        'revenue': {
            'total': total_revenue,
            'period_value': period_revenue,
            'trend': 'up' if period_revenue > 0 else 'stable',
            'percentage': min(revenue_change, 100)  # Cap at 100%
        },
        'active_users': {
            'total': active_users_total,
            'period_value': active_users_period,
            'trend': 'up' if active_users_period > 0 else 'stable',
            'percentage': min((active_users_period / max(active_users_total, 1) * 100), 100)
        },
        'unpaid_passports': {
            'total': unpaid_count,
            'overdue': overdue_count,
            'trend': 'down' if overdue_count == 0 else 'up',
            'percentage': overdue_count
        },
        'profit': {
            'total': profit,
            'margin': profit_margin,
            'trend': 'up' if profit > 0 else 'stable',
            'percentage': profit_margin
        }
    }
    
    return jsonify({
        'success': True,
        'period_days': period_days,
        'kpi_data': kpi_data
    })