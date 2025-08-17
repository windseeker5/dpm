"""
Simplified Flask routes for the AI Analytics Chatbot
Focused on reliability and simplicity over complex features
"""
import sqlite3
import json
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from datetime import datetime
import os

# Create the blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

def get_db_connection():
    """Get a simple database connection"""
    db_path = current_app.config.get('DATABASE_PATH', 'instance/minipass.db')
    if not db_path.startswith('/'):
        db_path = os.path.join(current_app.root_path, db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def execute_safe_query(query):
    """Execute a safe SELECT query and return results"""
    try:
        # Basic SQL injection prevention
        forbidden_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                return None, "Query contains forbidden keyword"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        # Convert results to list of dicts
        if results:
            columns = [description[0] for description in cursor.description]
            rows = [dict(zip(columns, row)) for row in results]
            return rows, None
        return [], None
    except Exception as e:
        return None, str(e)

def generate_response_for_question(question):
    """Generate a simple response based on the question"""
    question_lower = question.lower()
    
    # Revenue questions
    if 'revenue' in question_lower or 'money' in question_lower or 'income' in question_lower:
        query = """
            SELECT 
                COUNT(*) as total_passports,
                SUM(CASE WHEN paid = 1 THEN sold_amt ELSE 0 END) as total_revenue,
                SUM(CASE WHEN paid = 0 THEN sold_amt ELSE 0 END) as pending_revenue
            FROM passport
        """
        results, error = execute_safe_query(query)
        if results and len(results) > 0:
            data = results[0]
            answer = f"Total revenue: ${data.get('total_revenue', 0):,.2f} from {data.get('total_passports', 0)} passports. "
            if data.get('pending_revenue', 0) > 0:
                answer += f"There's also ${data.get('pending_revenue', 0):,.2f} in pending payments."
            return answer, query
        return "I couldn't fetch the revenue data. Please try again.", None
    
    # User questions
    elif 'user' in question_lower or 'member' in question_lower or 'people' in question_lower:
        query = """
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN created_at >= date('now', '-7 days') THEN 1 ELSE 0 END) as new_this_week,
                SUM(CASE WHEN created_at >= date('now', '-30 days') THEN 1 ELSE 0 END) as new_this_month
            FROM user
        """
        results, error = execute_safe_query(query)
        if results and len(results) > 0:
            data = results[0]
            answer = f"Total users: {data.get('total_users', 0)}. "
            answer += f"New users this week: {data.get('new_this_week', 0)}, this month: {data.get('new_this_month', 0)}."
            return answer, query
        return "I couldn't fetch the user data. Please try again.", None
    
    # Activity questions
    elif 'activit' in question_lower or 'event' in question_lower or 'class' in question_lower:
        query = """
            SELECT 
                COUNT(*) as total_activities,
                SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active_activities,
                SUM(CASE WHEN start_date >= date('now') THEN 1 ELSE 0 END) as upcoming
            FROM activity
        """
        results, error = execute_safe_query(query)
        if results and len(results) > 0:
            data = results[0]
            answer = f"Total activities: {data.get('total_activities', 0)} "
            answer += f"({data.get('active_activities', 0)} active, {data.get('upcoming', 0)} upcoming)."
            return answer, query
        return "I couldn't fetch the activity data. Please try again.", None
    
    # Signup questions
    elif 'signup' in question_lower or 'registration' in question_lower:
        query = """
            SELECT 
                COUNT(*) as total_signups,
                SUM(CASE WHEN paid = 1 THEN 1 ELSE 0 END) as paid_signups,
                SUM(CASE WHEN created_at >= date('now', '-7 days') THEN 1 ELSE 0 END) as recent_signups
            FROM signup
        """
        results, error = execute_safe_query(query)
        if results and len(results) > 0:
            data = results[0]
            answer = f"Total signups: {data.get('total_signups', 0)} "
            answer += f"({data.get('paid_signups', 0)} paid). "
            answer += f"Recent signups (last 7 days): {data.get('recent_signups', 0)}."
            return answer, query
        return "I couldn't fetch the signup data. Please try again.", None
    
    # Unpaid users
    elif 'unpaid' in question_lower or 'pending' in question_lower:
        query = """
            SELECT 
                u.email, u.first_name, u.last_name, 
                COUNT(s.id) as unpaid_signups
            FROM user u
            JOIN signup s ON u.id = s.user_id
            WHERE s.paid = 0
            GROUP BY u.id
            ORDER BY unpaid_signups DESC
            LIMIT 10
        """
        results, error = execute_safe_query(query)
        if results and len(results) > 0:
            answer = f"Found {len(results)} users with unpaid signups. "
            answer += f"Top user: {results[0].get('first_name', '')} {results[0].get('last_name', '')} "
            answer += f"with {results[0].get('unpaid_signups', 0)} unpaid signups."
            return answer, query
        return "No users with unpaid signups found.", query
    
    # Default response
    else:
        # Try to provide a general overview
        query = """
            SELECT 
                (SELECT COUNT(*) FROM user) as users,
                (SELECT COUNT(*) FROM activity WHERE active = 1) as activities,
                (SELECT COUNT(*) FROM signup) as signups,
                (SELECT SUM(sold_amt) FROM passport WHERE paid = 1) as revenue
        """
        results, error = execute_safe_query(query)
        if results and len(results) > 0:
            data = results[0]
            answer = f"Here's a quick overview: {data.get('users', 0)} users, "
            answer += f"{data.get('activities', 0)} active activities, "
            answer += f"{data.get('signups', 0)} total signups, "
            answer += f"${data.get('revenue', 0):,.2f} in revenue."
            return answer, query
        return f"I understand you're asking about: {question}. Could you please be more specific about what data you'd like to see?", None

@chatbot_bp.route('/')
def index():
    """Main chatbot interface"""
    # Simple auth check
    admin_email = session.get('admin')
    if not admin_email:
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))
    
    return render_template(
        'analytics_chatbot_simple.html',
        conversation_id='simple-' + datetime.now().strftime('%Y%m%d%H%M%S')
    )

@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a user question - simplified version"""
    
    # Simple auth check
    admin_email = session.get('admin')
    if not admin_email:
        return jsonify({
            'success': False,
            'error': 'Authentication required'
        }), 401
    
    # Get question from request
    if request.content_type and 'application/json' in request.content_type:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    question = data.get('question', '').strip()
    
    # Basic validation
    if not question:
        return jsonify({
            'success': False,
            'error': 'Question is required'
        }), 400
    
    if len(question) > 500:
        return jsonify({
            'success': False,
            'error': 'Question is too long (max 500 characters)'
        }), 400
    
    try:
        # Generate response based on question
        answer, sql_query = generate_response_for_question(question)
        
        response = {
            'success': True,
            'question': question,
            'answer': answer,
            'sql': sql_query,
            'conversation_id': data.get('conversation_id', 'simple'),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error processing question: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing your question: {str(e)}'
        }), 500

@chatbot_bp.route('/status')
def status():
    """Simple status endpoint"""
    return jsonify({
        'status': 'online',
        'provider': 'simple',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@chatbot_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@chatbot_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500