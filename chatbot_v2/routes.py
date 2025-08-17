"""
Flask routes for the AI Analytics Chatbot
"""
import asyncio
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_wtf.csrf import exempt

# Simplified imports for debugging
# from .ai_providers import provider_manager
# from .providers.ollama import create_ollama_provider
# from .query_engine import create_query_engine
# from .conversation import conversation_manager
# from .utils import get_current_admin_email, validate_question_length
# from .config import OLLAMA_BASE_URL, CHATBOT_ENABLE_OLLAMA


# Create the blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


def initialize_chatbot():
    """Initialize AI providers"""
    
    # Register Ollama provider if enabled
    if CHATBOT_ENABLE_OLLAMA:
        try:
            ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
            # Check if Ollama is actually available
            if ollama_provider.check_availability():
                provider_manager.register_provider(ollama_provider, is_primary=True)
                print("✅ Ollama provider registered successfully")
            else:
                print("⚠️ Ollama provider not available (server may not be running)")
                # Register a mock provider for testing
                from .providers.mock import create_mock_provider
                mock_provider = create_mock_provider()
                provider_manager.register_provider(mock_provider, is_primary=True)
                print("✅ Mock provider registered as fallback")
        except Exception as e:
            print(f"❌ Failed to register Ollama provider: {e}")
            # Register a mock provider for testing
            try:
                from .providers.mock import create_mock_provider
                mock_provider = create_mock_provider()
                provider_manager.register_provider(mock_provider, is_primary=True)
                print("✅ Mock provider registered as fallback")
            except Exception as mock_error:
                print(f"❌ Failed to register mock provider: {mock_error}")

# Initialize chatbot when module is imported
# COMMENTED OUT for debugging: initialize_chatbot()


@chatbot_bp.route('/')
def index():
    """Main chatbot interface"""
    
    # Simplified auth check
    admin_email = session.get('admin')
    if not admin_email:
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))
    
    # Mock data for testing
    messages = []
    conversation_id = 'test-conversation'
    available_models = [{'provider': 'mock', 'model': 'test-model', 'display_name': 'Mock Test Model'}]
    
    return render_template(
        'analytics_chatbot_modern.html',
        messages=messages,
        conversation_id=conversation_id,
        session_token='test-session',
        available_models=available_models,
        provider_status={'mock': {'available': True, 'models': ['test-model']}},
        current_time='Just now'
    )


@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a user question"""
    
    print("\n🚀 /chatbot/ask endpoint called!")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print(f"Request data: {request.get_data()}")
    
    # Simplified auth check
    admin_email = session.get('admin')
    print(f"Admin email: {admin_email}")
    if not admin_email:
        print("⚠️ Authentication failed, using fallback admin email for testing")
        admin_email = "test@example.com"  # TEMP: Allow testing without auth
    
    # Get request data (form data or JSON)
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
            'error': 'Invalid request data'
        }), 400
    
    question = data.get('question', '').strip()
    conversation_id = data.get('conversation_id')
    preferred_provider = data.get('provider')
    preferred_model = data.get('model')
    
    print(f"Question: {question}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Provider: {preferred_provider}")
    print(f"Model: {preferred_model}")
    
    # Simplified validation
    if not question or len(question) > 500:
        return jsonify({
            'success': False,
            'error': 'Invalid question length'
        }), 400
    
    try:
        # SIMPLIFIED MOCK RESPONSE FOR TESTING
        print(f"💬 Processing question: {question}")
        
        # Simple mock responses based on question content
        if 'revenue' in question.lower():
            answer = "Our total revenue this month is $15,420. This represents a 12% increase from last month."
            sql = "SELECT SUM(p.sold_amt) as total_revenue FROM passport p WHERE p.paid = 1 AND DATE(p.paid_date) >= DATE('now', 'start of month')"
            row_count = 1
        elif 'users' in question.lower():
            answer = "We currently have 142 active users, with 23 new signups this week."
            sql = "SELECT COUNT(*) as user_count FROM user WHERE active = 1"
            row_count = 1
        else:
            answer = f"I understand you're asking about: {question}. This is a test response from the chatbot system."
            sql = "SELECT COUNT(*) as total_records FROM user"
            row_count = 1
        
        response_data = {
            'success': True,
            'question': question,
            'answer': answer,
            'sql': sql,
            'columns': ['result'],
            'rows': [{'result': 'mock_data'}],
            'row_count': row_count,
            'ai_provider': 'mock',
            'ai_model': 'test-model',
            'processing_time_ms': 150
        }
        
        print(f"✅ Returning mock response: {response_data}")
        return jsonify(response_data)
    
    except Exception as e:
        current_app.logger.error(f"Error processing question: {e}")
        
        # Add error message to conversation
        if conversation_id:
            conversation_manager.add_error_message(conversation_id, str(e))
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@chatbot_bp.route('/status')
def provider_status():
    """Get AI provider status"""
    
    admin_email = get_current_admin_email()
    if not admin_email:
        return jsonify({'error': 'Authentication required'}), 401
    
    status = provider_manager.get_all_status()
    return jsonify(status)


@chatbot_bp.route('/conversation/<int:conversation_id>/messages')
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation"""
    
    admin_email = get_current_admin_email()
    if not admin_email:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        messages = conversation_manager.format_messages_for_display(conversation_id)
        return jsonify({
            'success': True,
            'messages': messages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/conversation/<int:conversation_id>/archive', methods=['POST'])
def archive_conversation(conversation_id):
    """Archive a conversation"""
    
    admin_email = get_current_admin_email()
    if not admin_email:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        conversation_manager.archive_conversation(conversation_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_bp.route('/conversations')
def list_conversations():
    """List user's conversations"""
    
    admin_email = get_current_admin_email()
    if not admin_email:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        conversations = conversation_manager.get_user_conversations(admin_email)
        conversation_list = []
        
        for conv in conversations:
            stats = conversation_manager.get_conversation_stats(conv.id)
            # Format for frontend display
            conversation_list.append({
                'id': conv.id,
                'title': f"Chat {conv.id}",
                'preview': f"{stats['message_counts']['user']} messages",
                'time': conv.updated_at.strftime('%b %d, %Y') if conv.updated_at else 'Recently'
            })
        
        return jsonify({
            'success': True,
            'conversations': conversation_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers
@chatbot_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@chatbot_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500