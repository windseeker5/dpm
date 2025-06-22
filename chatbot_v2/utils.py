"""
Utility functions for the chatbot module
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import session


def generate_session_token() -> str:
    """Generate a unique session token for chat conversations"""
    return uuid.uuid4().hex


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency values for display"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'CAD':
        return f"C${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    """Format datetime for display"""
    if not dt:
        return 'N/A'
    
    if format_type == 'date':
        return dt.strftime('%Y-%m-%d')
    elif format_type == 'time':
        return dt.strftime('%H:%M:%S')
    elif format_type == 'short':
        return dt.strftime('%Y-%m-%d %H:%M')
    else:  # full
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')


def calculate_processing_time(start_time: datetime, end_time: datetime) -> int:
    """Calculate processing time in milliseconds"""
    delta = end_time - start_time
    return int(delta.total_seconds() * 1000)


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Ensure it's not empty
    if not filename:
        filename = 'unnamed'
    return filename


def parse_json_safely(json_str: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string, return None if invalid"""
    try:
        return json.loads(json_str) if json_str else None
    except (json.JSONDecodeError, TypeError):
        return None


def get_current_admin_email() -> Optional[str]:
    """Get current admin email from session"""
    return session.get('admin')


def format_token_count(tokens: int) -> str:
    """Format token count for display"""
    if tokens >= 1000000:
        return f"{tokens / 1000000:.1f}M"
    elif tokens >= 1000:
        return f"{tokens / 1000:.1f}K"
    else:
        return str(tokens)


def format_cost(cost_cents: int) -> str:
    """Format cost in cents to dollar display"""
    if cost_cents == 0:
        return "Free"
    dollars = cost_cents / 100
    if dollars < 0.01:
        return f"{cost_cents}¢"
    else:
        return f"${dollars:.2f}"


def detect_query_intent(question: str) -> str:
    """Detect the intent of a user question"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['chart', 'graph', 'plot', 'visualize']):
        return 'visualization'
    elif any(word in question_lower for word in ['export', 'download', 'csv', 'pdf']):
        return 'export'
    elif any(word in question_lower for word in ['count', 'how many', 'total', 'sum']):
        return 'aggregation'
    elif any(word in question_lower for word in ['list', 'show', 'display', 'find']):
        return 'listing'
    elif any(word in question_lower for word in ['compare', 'difference', 'vs', 'versus']):
        return 'comparison'
    else:
        return 'general'


def extract_entities(question: str) -> Dict[str, List[str]]:
    """Extract entities from user question (basic implementation)"""
    import re
    
    entities = {
        'dates': [],
        'activities': [],
        'numbers': [],
        'emails': []
    }
    
    # Extract dates (simple patterns)
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
        r'\b(today|yesterday|tomorrow)\b',
        r'\b(last|this|next)\s+(week|month|year)\b'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, question, re.IGNORECASE)
        entities['dates'].extend(matches)
    
    # Extract numbers
    number_pattern = r'\b\d+\b'
    entities['numbers'] = re.findall(number_pattern, question)
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities['emails'] = re.findall(email_pattern, question)
    
    return entities


def generate_chart_config(chart_type: str, data: List[Dict], x_column: str, y_column: str) -> Dict[str, Any]:
    """Generate Chart.js configuration"""
    
    labels = [str(row.get(x_column, '')) for row in data]
    values = [row.get(y_column, 0) for row in data]
    
    config = {
        'type': chart_type,
        'data': {
            'labels': labels,
            'datasets': [{
                'label': y_column.replace('_', ' ').title(),
                'data': values,
                'borderWidth': 1
            }]
        },
        'options': {
            'responsive': True,
            'plugins': {
                'title': {
                    'display': True,
                    'text': f"{y_column.replace('_', ' ').title()} by {x_column.replace('_', ' ').title()}"
                }
            }
        }
    }
    
    # Customize colors based on chart type
    if chart_type == 'bar':
        config['data']['datasets'][0]['backgroundColor'] = 'rgba(54, 162, 235, 0.5)'
        config['data']['datasets'][0]['borderColor'] = 'rgba(54, 162, 235, 1)'
    elif chart_type == 'line':
        config['data']['datasets'][0]['backgroundColor'] = 'rgba(255, 99, 132, 0.1)'
        config['data']['datasets'][0]['borderColor'] = 'rgba(255, 99, 132, 1)'
        config['data']['datasets'][0]['fill'] = True
    elif chart_type == 'pie':
        colors = [
            'rgba(255, 99, 132, 0.8)',
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)'
        ]
        config['data']['datasets'][0]['backgroundColor'] = colors[:len(values)]
    
    return config


def validate_question_length(question: str, max_length: int = 500) -> tuple[bool, str]:
    """Validate question length"""
    if not question or not question.strip():
        return False, "Question cannot be empty"
    
    if len(question) > max_length:
        return False, f"Question too long (max {max_length} characters)"
    
    return True, ""


def clean_sql_for_display(sql: str) -> str:
    """Clean SQL for better display formatting"""
    import re
    
    # Add line breaks for better readability
    sql = re.sub(r'\bFROM\b', '\nFROM', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bWHERE\b', '\nWHERE', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bJOIN\b', '\nJOIN', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bGROUP BY\b', '\nGROUP BY', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bORDER BY\b', '\nORDER BY', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bLIMIT\b', '\nLIMIT', sql, flags=re.IGNORECASE)
    
    return sql.strip()


class MessageFormatter:
    """Format chat messages for display"""
    
    @staticmethod
    def format_user_message(content: str, timestamp: datetime) -> Dict[str, Any]:
        """Format user message"""
        return {
            'type': 'user',
            'content': content,
            'timestamp': format_datetime(timestamp, 'short'),
            'avatar_class': 'avatar-user'
        }
    
    @staticmethod
    def format_assistant_message(content: str, timestamp: datetime, 
                                 sql: Optional[str] = None,
                                 chart_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Format assistant message"""
        return {
            'type': 'assistant',
            'content': content,
            'timestamp': format_datetime(timestamp, 'short'),
            'avatar_class': 'avatar-assistant',
            'sql': clean_sql_for_display(sql) if sql else None,
            'chart_data': chart_data
        }
    
    @staticmethod
    def format_error_message(error: str, timestamp: datetime) -> Dict[str, Any]:
        """Format error message"""
        return {
            'type': 'error',
            'content': f"Error: {error}",
            'timestamp': format_datetime(timestamp, 'short'),
            'avatar_class': 'avatar-error'
        }
    
    @staticmethod
    def format_system_message(content: str, timestamp: datetime) -> Dict[str, Any]:
        """Format system message"""
        return {
            'type': 'system',
            'content': content,
            'timestamp': format_datetime(timestamp, 'short'),
            'avatar_class': 'avatar-system'
        }