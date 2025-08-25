# Components Directory

This directory contains production-ready, reusable components for the Minipass application.

## Available Components

### KPICard (`kpi_card.py`)
Production-ready KPI card generator with security, caching, and resilience features.

**Quick Start:**
```python
from components.kpi_card import generate_kpi_card

# Generate a revenue card
card = generate_kpi_card('revenue', activity_id=123)
print(card['formatted_total'])  # '$1,234.56'
```

**Features:**
- 🛡️ Input validation with Pydantic schemas
- ⚡ Smart caching with configurable TTLs
- 🔄 Circuit breaker pattern for database resilience
- 📱 Mobile and desktop responsive variants
- 🎯 Compatible with existing dashboard formats
- 🚀 Easy integration with Flask routes and templates

**Supported Card Types:**
- `revenue` - Financial revenue metrics
- `active_users` - User activity tracking
- `active_passports` - Active passport counts
- `passports_created` - Creation rate tracking
- `pending_signups` - Signup conversion metrics
- `unpaid_passports` - Payment follow-up tracking
- `profit` - Calculated profit margins

**Documentation:** See `/doc/kpi_card_component_documentation.md`

## Usage Examples

### Single Card Generation
```python
from components.kpi_card import generate_kpi_card

card = generate_kpi_card(
    card_type='revenue',
    activity_id=123,        # Optional
    period='30d',          # '7d', '30d', '90d'
    device_type='mobile',  # 'mobile' or 'desktop'
    force_refresh=True     # Optional cache refresh
)
```

### Dashboard Integration
```python
from components.kpi_card import generate_dashboard_cards

# Generate all standard KPI cards
dashboard = generate_dashboard_cards(activity_id=123)
cards = dashboard['cards']
```

### Flask Route Integration
```python
from flask import jsonify
from components.kpi_card import generate_kpi_card

@app.route('/api/kpi/<card_type>')
def get_kpi_card(card_type):
    card = generate_kpi_card(card_type)
    return jsonify(card)
```

### Template Integration
```html
<div class="{{ card.css_classes.card }}">
    <h3 class="{{ card.css_classes.title }}">{{ card.title }}</h3>
    <div class="{{ card.css_classes.value }}">{{ card.formatted_total }}</div>
    <div class="{{ card.trend_color }}">
        <i class="{{ card.trend_icon }}"></i>
        {{ card.formatted_change }}
    </div>
</div>
```

## Testing

Run the test suite to verify component functionality:

```bash
# Activate virtual environment
source venv/bin/activate

# Run component tests
python test/test_kpi_card_component.py

# Run integration examples
python test/example_integration.py
```

## File Structure

```
components/
├── __init__.py                    # Package exports
├── kpi_card.py                   # KPICard component
└── README.md                     # This file

test/
├── test_kpi_card_component.py    # Unit tests
└── example_integration.py        # Integration examples

doc/
└── kpi_card_component_documentation.md  # Full documentation
```

## Design Principles

1. **Security First**: Input validation, SQL injection prevention, secure error handling
2. **Performance**: Caching, circuit breakers, efficient data structures
3. **Reliability**: Graceful degradation, comprehensive error handling, fallback data
4. **Compatibility**: Works with existing dashboard formats and templates
5. **Extensibility**: Easy to add new card types and customize behavior

## Adding New Components

When adding new components to this directory:

1. Create the component file in `/app/components/`
2. Add exports to `__init__.py`
3. Create tests in `/test/test_[component_name].py`
4. Add documentation in `/doc/[component_name]_documentation.md`
5. Update this README with usage examples

## Best Practices

- Always validate inputs using Pydantic or similar validation
- Implement proper error handling with logging
- Use caching for expensive operations
- Support both mobile and desktop variants
- Maintain compatibility with existing code
- Write comprehensive tests
- Document all public APIs