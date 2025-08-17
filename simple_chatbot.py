"""
Simple working chatbot implementation
"""
from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template, flash

# Create the blueprint
simple_chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

@simple_chatbot_bp.route('/')
def index():
    """Main chatbot interface"""
    if not session.get('admin'):
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))
    
    return render_template(
        'analytics_chatbot_modern.html',
        messages=[],
        conversation_id='simple-123',
        session_token='simple-session',
        available_models=[
            {'provider': 'ollama', 'model': 'simple-model', 'display_name': 'Simple Model'},
            {'provider': 'ollama', 'model': 'llama2', 'display_name': 'Llama 2'},
            {'provider': 'ollama', 'model': 'codellama', 'display_name': 'Code Llama'},
            {'provider': 'ollama', 'model': 'mistral', 'display_name': 'Mistral'},
            {'provider': 'ollama', 'model': 'nonexistent-model', 'display_name': 'Unavailable Model'}
        ],
        provider_status={'simple': {'available': True, 'models': ['simple-model']}},
        current_time='Just now'
    )

@simple_chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a user question"""
    print("\n🚀 Simple chatbot /ask endpoint called!")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    
    try:
        # Handle both form data and JSON
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            print(f"Parsed JSON data: {data}")
        else:
            data = request.form.to_dict()
            print(f"Parsed form data: {data}")
        
        if not data:
            print("❌ No data received!")
            return jsonify({
                'success': False,
                'error': 'No data received'
            }), 400
        
        question = data.get('question', '').strip()
        print(f"Question: {question}")
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        # Generate mock response based on question
        if 'revenue' in question.lower():
            answer = "Our total revenue this month is $15,420. This represents a 12% increase from last month."
            sql = "SELECT SUM(p.sold_amt) as total_revenue FROM passport p WHERE p.paid = 1 AND DATE(p.paid_date) >= DATE('now', 'start of month')"
        elif 'users' in question.lower():
            answer = "We currently have 142 active users, with 23 new signups this week."
            sql = "SELECT COUNT(*) as user_count FROM user WHERE active = 1"
        else:
            answer = f"I understand you're asking about: {question}. This is a working response from the simplified chatbot!"
            sql = "SELECT COUNT(*) as total_records FROM user"
        
        response = {
            'success': True,
            'question': question,
            'answer': answer,
            'sql': sql,
            'columns': ['result'],
            'rows': [{'result': 'simple_data'}],
            'row_count': 1,
            'ai_provider': 'simple',
            'ai_model': 'simple-model',
            'processing_time_ms': 100
        }
        
        print(f"✅ Returning response: {response}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in ask_question: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@simple_chatbot_bp.route('/check-model', methods=['POST'])
def check_model():
    """Check if a specific model is available"""
    try:
        # Handle both form data and JSON
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        model = data.get('model', '').strip()
        print(f"🔍 Checking model availability: {model}")
        
        if not model:
            return jsonify({
                'success': False,
                'available': False,
                'error': 'Model name is required'
            }), 400
        
        # Simple mock implementation - in a real app, this would check actual model availability
        available_models = ['simple-model', 'llama2', 'codellama', 'mistral']
        is_available = model in available_models
        
        print(f"✅ Model {model} availability: {is_available}")
        
        return jsonify({
            'success': True,
            'available': is_available,
            'model': model,
            'provider': 'simple' if is_available else None
        })
        
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return jsonify({
            'success': False,
            'available': False,
            'error': f'Server error: {str(e)}'
        }), 500

@simple_chatbot_bp.route('/status')
def status():
    """Get provider status"""
    return jsonify({
        'simple': {
            'available': True,
            'models': ['simple-model']
        }
    })