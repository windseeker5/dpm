#!/usr/bin/env python3
"""
Example integration of KPICard component with Flask application

This demonstrates how to use the KPICard component in your Flask routes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from components.kpi_card import generate_kpi_card, generate_dashboard_cards, clear_kpi_cache


def create_example_app():
    """Create a Flask app with KPI card endpoints"""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minipass.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Example endpoint for single KPI card
    @app.route('/api/kpi-card/<card_type>')
    def get_kpi_card(card_type):
        """Get a single KPI card"""
        try:
            # Get query parameters
            activity_id = request.args.get('activity_id', type=int)
            period = request.args.get('period', '7d')
            device_type = request.args.get('device_type', 'desktop')
            force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
            
            # Generate card
            card_data = generate_kpi_card(
                card_type=card_type,
                activity_id=activity_id,
                period=period,
                device_type=device_type,
                force_refresh=force_refresh
            )
            
            return jsonify(card_data)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Example endpoint for dashboard cards
    @app.route('/api/dashboard-cards')
    def get_dashboard_cards():
        """Get all dashboard KPI cards"""
        try:
            # Get query parameters
            activity_id = request.args.get('activity_id', type=int)
            period = request.args.get('period', '7d')
            device_type = request.args.get('device_type', 'desktop')
            
            # Generate all cards
            cards_data = generate_dashboard_cards(
                activity_id=activity_id,
                period=period,
                device_type=device_type
            )
            
            return jsonify(cards_data)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Example endpoint for cache management
    @app.route('/api/kpi-cache', methods=['DELETE'])
    def clear_cache():
        """Clear KPI cache"""
        try:
            pattern = request.args.get('pattern')
            result = clear_kpi_cache(pattern)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Example endpoint showing how to replace existing KPI endpoints
    @app.route('/api/activity-kpis/<int:activity_id>')
    def get_activity_kpis(activity_id):
        """
        Replacement for existing activity KPI endpoint using new component
        This maintains compatibility with existing frontend code
        """
        try:
            period = request.args.get('period', '7d')
            device_type = request.args.get('device_type', 'desktop')
            
            # Generate all cards for the activity
            cards_result = generate_dashboard_cards(
                activity_id=activity_id,
                period=period,
                device_type=device_type
            )
            
            if not cards_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate cards'
                }), 500
            
            # Transform to match existing API structure
            cards = cards_result.get('cards', {})
            
            # Build response in expected format
            kpi_data = {}
            for card_id, card in cards.items():
                card_type = card.get('card_type')
                if card_type:
                    kpi_data[card_type] = {
                        'total': card.get('total', 0),
                        'change': card.get('change', 0),
                        'percentage': card.get('percentage', 0),
                        'trend': card.get('trend_direction', 'stable'),
                        'trend_data': card.get('trend_data', [])
                    }
            
            return jsonify({
                'success': True,
                'period': period,
                'kpi_data': kpi_data,
                'meta': {
                    'generated_with': 'KPICard component v1.0.0',
                    'total_cards': len(cards),
                    'activity_id': activity_id
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app


def demo_usage():
    """Demo the KPICard component usage"""
    
    print("🚀 KPICard Component Integration Examples")
    print("=" * 50)
    
    print("\n1️⃣ Basic Usage:")
    print("```python")
    print("from components.kpi_card import generate_kpi_card")
    print("")
    print("# Generate revenue card for desktop")
    print("card = generate_kpi_card('revenue')")
    print("print(card['formatted_total'])  # '$1,234.56'")
    print("```")
    
    print("\n2️⃣ Activity-Specific Cards:")
    print("```python")
    print("# Generate mobile-optimized card for specific activity")
    print("card = generate_kpi_card(")
    print("    card_type='active_users',")
    print("    activity_id=123,")
    print("    device_type='mobile',")
    print("    period='30d'")
    print(")")
    print("```")
    
    print("\n3️⃣ Dashboard Integration:")
    print("```python")
    print("from components.kpi_card import generate_dashboard_cards")
    print("")
    print("# Generate all dashboard cards")
    print("dashboard = generate_dashboard_cards(activity_id=123)")
    print("for card_id, card_data in dashboard['cards'].items():")
    print("    print(f'{card_data[\"title\"]}: {card_data[\"formatted_total\"]}')")
    print("```")
    
    print("\n4️⃣ Flask Route Integration:")
    print("```python")
    print("@app.route('/api/kpi/<card_type>')")
    print("def get_kpi(card_type):")
    print("    card = generate_kpi_card(card_type)")
    print("    return jsonify(card)")
    print("```")
    
    print("\n5️⃣ Template Integration:")
    print("```html")
    print("<!-- In your Jinja2 template -->")
    print("<div class='{{ card.css_classes.card }}'>")
    print("    <div class='{{ card.css_classes.header }}'>")
    print("        <h3 class='{{ card.css_classes.title }}'>{{ card.title }}</h3>")
    print("    </div>")
    print("    <div class='{{ card.css_classes.body }}'>")
    print("        <div class='{{ card.css_classes.value }}'>{{ card.formatted_total }}</div>")
    print("        <div class='{{ card.trend_color }}'>")
    print("            <i class='{{ card.trend_icon }}'></i>")
    print("            {{ card.formatted_change }}")
    print("        </div>")
    print("    </div>")
    print("</div>")
    print("```")
    
    print("\n6️⃣ Cache Management:")
    print("```python")
    print("from components.kpi_card import clear_kpi_cache")
    print("")
    print("# Clear all cache")
    print("clear_kpi_cache()")
    print("")
    print("# Clear specific pattern")
    print("clear_kpi_cache('revenue')")
    print("```")
    
    print("\n7️⃣ Error Handling:")
    print("```python")
    print("card = generate_kpi_card('revenue')")
    print("if card.get('success'):")
    print("    print(f'Generated in {card[\"generation_time_ms\"]}ms')")
    print("else:")
    print("    print(f'Error: {card[\"error\"]}')")
    print("```")
    
    print("\n" + "=" * 50)
    print("✨ Key Features:")
    print("- 🛡️  Production-ready with security hardening")
    print("- ⚡  Smart caching with configurable TTLs")
    print("- 🔄  Circuit breaker for database resilience")
    print("- 📱  Mobile and desktop responsive variants")
    print("- 🎯  Maintains compatibility with existing frontend")
    print("- 🚀  Easy to integrate and extend")


if __name__ == '__main__':
    demo_usage()
    
    print("\n🖥️  To run the example Flask app:")
    print("```bash")
    print("python test/example_integration.py")
    print("# Then visit: http://localhost:5000/api/kpi-card/revenue")
    print("```")