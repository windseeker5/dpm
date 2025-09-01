"""
KPI Card Renderer - Helper functions to render new ApexCharts KPI cards
Integrates with get_kpi_data() function from utils.py
"""
from flask import render_template
from utils import get_kpi_data


def render_revenue_card(activity_id=None, period='7d'):
    """Render revenue KPI card with line chart"""
    data = get_kpi_data(activity_id=activity_id, period=period)
    
    revenue_data = data.get('revenue', {})
    current_value = revenue_data.get('current', 0)
    change = revenue_data.get('change', 0)
    trend = revenue_data.get('trend_data', [0] * 7)
    
    # Format value as currency
    formatted_value = f"${current_value:,.0f}"
    
    # Format change with proper sign and color class
    if change > 0:
        change_class = "text-success"
        change_icon = "ti-trending-up"
    elif change < 0:
        change_class = "text-danger" 
        change_icon = "ti-trending-down"
    else:
        change_class = "text-muted"
        change_icon = "ti-minus"
    
    return render_template('kpi_card_line.html',
                          title='Revenue',
                          card_id='revenue',
                          value=formatted_value,
                          change=abs(change) if change != 0 else 0,
                          change_class=change_class,
                          change_icon=change_icon,
                          trend_data=trend)


def render_active_users_card(activity_id=None, period='7d'):
    """Render active users KPI card with bar chart"""
    data = get_kpi_data(activity_id=activity_id, period=period)
    
    active_users_data = data.get('active_users', {})
    current_value = active_users_data.get('current', 0)
    change = active_users_data.get('change', 0) or 0
    trend = active_users_data.get('trend_data', [0] * 7)
    
    # Format change with proper sign and color class
    if change > 0:
        change_class = "text-success"
        change_icon = "ti-trending-up"
    elif change < 0:
        change_class = "text-danger"
        change_icon = "ti-trending-down"
    else:
        change_class = "text-muted"
        change_icon = "ti-minus"
    
    return render_template('kpi_card_bar.html',
                          title='Active Users',
                          card_id='active_users',
                          value=f"{current_value:,}",
                          change=abs(change) if change != 0 else 0,
                          change_class=change_class,
                          change_icon=change_icon,
                          trend_data=trend)


def render_passports_created_card(activity_id=None, period='7d'):
    """Render passports created KPI card with bar chart"""
    data = get_kpi_data(activity_id=activity_id, period=period)
    
    passports_data = data.get('passports_created', {})
    current_value = passports_data.get('current', 0)
    change = passports_data.get('change', 0) or 0
    trend = passports_data.get('trend_data', [0] * 7)
    
    # Format change with proper sign and color class
    if change > 0:
        change_class = "text-success"
        change_icon = "ti-trending-up"
    elif change < 0:
        change_class = "text-danger"
        change_icon = "ti-trending-down"
    else:
        change_class = "text-muted"
        change_icon = "ti-minus"
    
    return render_template('kpi_card_bar.html',
                          title='Passports Created',
                          card_id='passports_created',
                          value=f"{current_value:,}",
                          change=abs(change) if change != 0 else 0,
                          change_class=change_class,
                          change_icon=change_icon,
                          trend_data=trend)


def render_passports_unpaid_card(activity_id=None, period='7d'):
    """Render passports unpaid KPI card with bar chart"""
    data = get_kpi_data(activity_id=activity_id, period=period)
    
    unpaid_data = data.get('unpaid_passports', {})
    current_value = unpaid_data.get('current', 0)
    change = unpaid_data.get('change', 0) or 0
    trend = unpaid_data.get('trend_data', [0] * 7)
    
    # Format change with proper sign and color class
    if change > 0:
        change_class = "text-success"
        change_icon = "ti-trending-up"
    elif change < 0:
        change_class = "text-danger"
        change_icon = "ti-trending-down"
    else:
        change_class = "text-muted"
        change_icon = "ti-minus"
    
    return render_template('kpi_card_bar.html',
                          title='Passports Unpaid',
                          card_id='unpaid_passports',
                          value=f"{current_value:,}",
                          change=abs(change) if change != 0 else 0,
                          change_class=change_class,
                          change_icon=change_icon,
                          trend_data=trend)