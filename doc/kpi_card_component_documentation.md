# KPICard Component Documentation

## Overview

The KPICard component provides a production-ready, secure, and scalable solution for generating KPI (Key Performance Indicator) card data in the Minipass application. It features comprehensive validation, caching, error handling, and security measures.

## Features

### 🛡️ Security & Validation
- **Input Validation**: Pydantic schemas for type-safe parameter validation
- **SQL Injection Prevention**: Parameter sanitization and query validation
- **Circuit Breaker Pattern**: Database resilience with automatic failover
- **Error Handling**: Comprehensive logging and graceful degradation

### ⚡ Performance & Scalability
- **Smart Caching**: In-memory cache with configurable TTLs per card type
- **Fallback Data**: Graceful degradation when data sources fail
- **Bulk Generation**: Efficient generation of multiple cards
- **Response Time Tracking**: Built-in performance monitoring

### 📱 Responsive Design
- **Device Types**: Mobile and desktop optimized variants
- **CSS Classes**: Pre-configured responsive CSS class sets
- **Icon Integration**: Tabler.io icon support with proper formatting

### 🔄 Compatibility
- **Dual Format Support**: Compatible with both dashboard.html and activity_dashboard.html
- **Legacy API Support**: Drop-in replacement for existing KPI endpoints
- **Template Integration**: Easy Jinja2 template integration

## Supported Card Types

| Card Type | Description | Data Source |
|-----------|-------------|-------------|
| `revenue` | Financial revenue data | Passport payments |
| `active_users` | User activity metrics | User signups and activity |
| `active_passports` | Active passport count | Passport status |
| `passports_created` | New passport creation rate | Passport creation dates |
| `pending_signups` | Signup conversion tracking | Signup status |
| `unpaid_passports` | Payment follow-up metrics | Payment status |
| `profit` | Calculated profit margins | Revenue minus expenses |

## API Reference

### Core Class: `KPICard`

```python
from components.kpi_card import KPICard

kpi = KPICard()
card_data = kpi.generate_card(
    card_type='revenue',
    activity_id=None,      # Optional: Activity-specific data
    period='7d',           # '7d', '30d', or '90d'
    device_type='desktop', # 'mobile' or 'desktop'
    force_refresh=False    # Force cache refresh
)
```

### Convenience Functions

#### Generate Single Card
```python
from components.kpi_card import generate_kpi_card

card = generate_kpi_card('revenue', activity_id=123, device_type='mobile')
```

#### Generate Dashboard Cards
```python
from components.kpi_card import generate_dashboard_cards

dashboard = generate_dashboard_cards(activity_id=123, period='30d')
# Returns all 7 standard KPI cards
```

#### Cache Management
```python
from components.kpi_card import clear_kpi_cache

# Clear all cache
clear_kpi_cache()

# Clear specific pattern
clear_kpi_cache('revenue')
```

## Data Structure

### Response Format

```python
{
    # Metadata
    'card_id': 'kpi_revenue_global_7d_desktop_a1b2c3d4',
    'card_type': 'revenue',
    'title': 'Revenue',
    'activity_id': None,  # or integer for activity-specific
    'period': '7d',
    'device_type': 'desktop',
    'generated_at': '2024-08-24T12:34:56.789Z',
    'success': True,
    
    # Data Values
    'total': 1234.56,
    'formatted_total': '$1,234.56',
    'change': 15.2,
    'formatted_change': '+15.2%',
    'trend_data': [100, 120, 110, 130, 145, 140, 150],
    
    # Display Properties
    'prefix': '$',
    'trend_direction': 'up',      # 'up', 'down', 'stable'
    'trend_icon': 'ti ti-trending-up',
    'trend_color': 'text-success',
    
    # Responsive Design
    'is_mobile': False,
    'css_classes': {
        'card': 'card mb-4',
        'header': 'card-header',
        'body': 'card-body',
        'title': 'text-muted mb-2',
        'value': 'h2 mb-3',
        'trend': 'text-sm'
    },
    
    # Compatibility Fields
    'percentage': 15.2,           # For activity_dashboard.html
    'trend': 'up',               # For activity_dashboard.html
    'nested_data': {             # For dashboard.html
        '7d': {
            'revenue': {
                'total': 1234.56,
                'change': 15.2,
                'trend_data': [...]
            }
        }
    },
    
    # Performance
    'cache_hit': False,
    'generation_time_ms': 12.34
}
```

### Error Response Format

```python
{
    'success': False,
    'error': 'Invalid input parameters: card_type must be one of...',
    'error_type': 'validation',  # 'validation' or 'system'
    'generation_time_ms': 5.67,
    'debug_info': 'Detailed error info (if debug=True)'
}
```

## Integration Examples

### Flask Route Integration

```python
from flask import Flask, jsonify, request
from components.kpi_card import generate_kpi_card, generate_dashboard_cards

@app.route('/api/kpi/<card_type>')
def get_kpi_card(card_type):
    """Get single KPI card with query parameters"""
    try:
        card = generate_kpi_card(
            card_type=card_type,
            activity_id=request.args.get('activity_id', type=int),
            period=request.args.get('period', '7d'),
            device_type=request.args.get('device_type', 'desktop'),
            force_refresh=request.args.get('force_refresh') == 'true'
        )
        return jsonify(card)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard-cards')
def get_dashboard_cards():
    """Get all dashboard cards"""
    return jsonify(generate_dashboard_cards(
        activity_id=request.args.get('activity_id', type=int),
        period=request.args.get('period', '7d')
    ))
```

### Template Integration

#### Jinja2 Template (dashboard.html compatibility)
```html
<!-- Using nested data structure -->
{% set revenue_data = kpi_data.nested_data['7d']['revenue'] %}
<div class="card">
    <div class="card-body">
        <h3 class="card-title">Revenue</h3>
        <div class="h2">${{ "%.2f"|format(revenue_data.total) }}</div>
        <div class="text-success">
            <i class="ti ti-trending-up"></i>
            +{{ revenue_data.change }}%
        </div>
    </div>
</div>
```

#### Using KPICard Component Data
```html
<!-- Using full card data structure -->
<div class="{{ card.css_classes.card }}">
    <div class="{{ card.css_classes.header }}">
        <h3 class="{{ card.css_classes.title }}">{{ card.title }}</h3>
    </div>
    <div class="{{ card.css_classes.body }}">
        <div class="{{ card.css_classes.value }}">{{ card.formatted_total }}</div>
        <div class="{{ card.trend_color }}">
            <i class="{{ card.trend_icon }}"></i>
            {{ card.formatted_change }}
        </div>
    </div>
</div>
```

### JavaScript Integration

```javascript
// Fetch single card
async function fetchKPICard(cardType, activityId = null) {
    const params = new URLSearchParams({
        ...(activityId && { activity_id: activityId }),
        device_type: window.innerWidth < 768 ? 'mobile' : 'desktop'
    });
    
    const response = await fetch(`/api/kpi/${cardType}?${params}`);
    const card = await response.json();
    
    if (card.success) {
        updateKPIDisplay(card);
    } else {
        console.error('KPI card error:', card.error);
    }
}

// Update KPI display
function updateKPIDisplay(card) {
    const element = document.getElementById(card.card_id);
    if (element) {
        element.querySelector('.kpi-value').textContent = card.formatted_total;
        element.querySelector('.kpi-trend').textContent = card.formatted_change;
        element.querySelector('.kpi-trend').className = `kpi-trend ${card.trend_color}`;
        element.querySelector('.kpi-icon').className = card.trend_icon;
    }
}
```

## Configuration

### Cache TTL Settings
The component uses different cache TTLs based on data volatility:

```python
cache_ttls = {
    'revenue': 300,           # 5 minutes - financial data changes frequently
    'active_users': 180,      # 3 minutes - user activity changes often
    'active_passports': 600,  # 10 minutes - passport data more stable
    'passports_created': 900, # 15 minutes - creation counts stable
    'pending_signups': 120,   # 2 minutes - signup status changes quickly
    'unpaid_passports': 300,  # 5 minutes - payment status changes
    'profit': 600            # 10 minutes - calculated metric
}
```

### Circuit Breaker Settings
```python
max_failures = 5      # Circuit opens after 5 consecutive failures
circuit_timeout = 60  # Retry after 60 seconds when circuit is open
```

## Security Considerations

### Input Validation
- All parameters validated with Pydantic schemas
- Type checking and range validation
- SQL injection prevention through parameter sanitization

### Query Safety
```python
# Dangerous patterns blocked:
dangerous_patterns = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
    'EXEC', 'EXECUTE', 'UNION', '--', '/*', '*/', ';'
]
```

### Error Handling
- Sensitive error details only shown in debug mode
- Circuit breaker prevents cascade failures
- Graceful fallback to default data

## Performance Optimization

### Caching Strategy
1. **Cache Key Generation**: Unique keys based on card type, activity, period, and device
2. **TTL Management**: Different TTLs based on data volatility
3. **Cache Cleanup**: Automatic cleanup of expired entries
4. **Cache Eviction**: LRU eviction when cache size limit reached

### Database Optimization
1. **Circuit Breaker**: Prevents database overload during failures
2. **Connection Pooling**: Uses existing SQLAlchemy connection pooling
3. **Query Optimization**: Leverages existing optimized `get_kpi_stats` function
4. **Fallback Data**: Reduces database load during failures

## Migration Guide

### From Existing KPI Endpoints

#### Before (existing code):
```python
@app.route("/api/activity-kpis/<int:activity_id>")
def get_activity_kpis_api(activity_id):
    kpi_stats = get_kpi_stats(activity_id=activity_id)
    period_data = kpi_stats.get('7d', {})
    
    kpi_data = {
        'revenue': {
            'total': period_data.get('revenue', 0),
            'change': period_data.get('revenue_change', 0),
            'trend_data': period_data.get('revenue_trend', [])
        }
    }
    
    return jsonify({'success': True, 'kpi_data': kpi_data})
```

#### After (using KPICard component):
```python
from components.kpi_card import generate_dashboard_cards

@app.route("/api/activity-kpis/<int:activity_id>")
def get_activity_kpis_api(activity_id):
    dashboard = generate_dashboard_cards(activity_id=activity_id)
    
    if not dashboard.get('success'):
        return jsonify({'success': False, 'error': 'Failed to generate cards'}), 500
    
    # Transform to existing format for compatibility
    kpi_data = {}
    for card_id, card in dashboard['cards'].items():
        card_type = card.get('card_type')
        if card_type:
            kpi_data[card_type] = {
                'total': card.get('total', 0),
                'change': card.get('change', 0),
                'percentage': card.get('percentage', 0),
                'trend': card.get('trend_direction', 'stable'),
                'trend_data': card.get('trend_data', [])
            }
    
    return jsonify({'success': True, 'kpi_data': kpi_data})
```

## Testing

### Unit Tests
```bash
# Run component tests
python test/test_kpi_card_component.py

# Run integration tests
python test/example_integration.py
```

### Test Coverage
- ✅ Input validation
- ✅ Cache functionality
- ✅ Circuit breaker patterns
- ✅ Error handling
- ✅ Data format compatibility
- ✅ Device type variants
- ✅ Security validations

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
**Problem**: `SQLAlchemy instance not registered with Flask app`
**Solution**: Ensure Flask application context is active
```python
with app.app_context():
    card = generate_kpi_card('revenue')
```

#### 2. Cache Not Working
**Problem**: Cache misses on every request
**Solution**: Check cache key generation and TTL settings
```python
# Debug cache
from components.kpi_card import kpi_card_generator
stats = kpi_card_generator.get_cache_stats()
print(stats)
```

#### 3. Circuit Breaker Open
**Problem**: Circuit breaker preventing database access
**Solution**: Check database connectivity and error logs
```python
# Reset circuit breaker
kpi_card_generator.circuit_breakers.clear()
```

#### 4. Icon Encoding Issues
**Problem**: Icons showing as `â��` instead of proper icons
**Solution**: Component uses full `ti ti-*` format to prevent encoding issues
```python
# Correct format used internally
trend_icon = "ti ti-trending-up"  # ✅ Correct
```

## Best Practices

### 1. Error Handling
```python
# Always check for success
card = generate_kpi_card('revenue')
if card.get('success'):
    print(f"Revenue: {card['formatted_total']}")
else:
    print(f"Error: {card['error']}")
```

### 2. Performance
```python
# Use bulk generation for multiple cards
dashboard = generate_dashboard_cards()
# More efficient than multiple individual calls
```

### 3. Caching
```python
# Use appropriate cache refresh strategy
card = generate_kpi_card('revenue', force_refresh=True)  # Only when needed
```

### 4. Mobile Optimization
```python
# Detect device type
device_type = 'mobile' if request.user_agent.is_mobile else 'desktop'
card = generate_kpi_card('revenue', device_type=device_type)
```

## Future Enhancements

### Planned Features
- **Redis Integration**: Replace in-memory cache with Redis for scalability
- **Real-time Updates**: WebSocket support for live KPI updates
- **Custom Themes**: Configurable color schemes and styling
- **Export Functions**: PDF and Excel export capabilities
- **Advanced Analytics**: Trend analysis and forecasting
- **A/B Testing**: Support for experimental KPI variants

### Extension Points
- **Custom Card Types**: Easy addition of new card types
- **Data Sources**: Support for external data sources
- **Formatters**: Custom formatting functions
- **Validators**: Custom validation rules
- **Themes**: Custom CSS theme support

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review test examples in `/test/` directory
3. Check component logs for detailed error information
4. Use debug mode for additional error details