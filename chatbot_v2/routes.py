"""
Flask routes for the AI Analytics Chatbot
"""
import asyncio
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app

from .ai_providers import provider_manager
from .providers.ollama import create_ollama_provider
from .query_engine import create_query_engine
from .conversation import conversation_manager
from .utils import get_current_admin_email, validate_question_length
from .config import OLLAMA_BASE_URL, CHATBOT_ENABLE_OLLAMA


# Create the blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


def initialize_chatbot():
    """Initialize AI providers"""
    
    # Register Ollama provider if enabled
    if CHATBOT_ENABLE_OLLAMA:
        try:
            ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
            provider_manager.register_provider(ollama_provider, is_primary=True)
            print("✅ Ollama provider registered successfully")
        except Exception as e:
            print(f"❌ Failed to register Ollama provider: {e}")

# Initialize chatbot when module is imported
initialize_chatbot()


@chatbot_bp.route('/')
def index():
    """Main chatbot interface"""
    
    # Check admin authentication
    admin_email = get_current_admin_email()
    if not admin_email:
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))
    
    # Get or create conversation
    conversation = conversation_manager.get_or_create_conversation(admin_email)
    
    # Get formatted messages for display
    messages = conversation_manager.format_messages_for_display(conversation.id)
    
    # Get available AI providers and models
    provider_status = provider_manager.get_all_status()
    available_models = []
    
    for provider_name, status in provider_status.items():
        if status['available']:
            for model in status['models']:
                available_models.append({
                    'provider': provider_name,
                    'model': model,
                    'display_name': f"{provider_name}: {model}"
                })
    
    return render_template(
        'analytics_chatbot.html',
        messages=messages,
        conversation_id=conversation.id,
        session_token=conversation.session_token,
        available_models=available_models,
        provider_status=provider_status
    )


@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a user question"""
    
    # Check admin authentication
    admin_email = get_current_admin_email()
    if not admin_email:
        return jsonify({
            'success': False,
            'error': 'Authentication required'
        }), 401
    
    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'Invalid request data'
        }), 400
    
    question = data.get('question', '').strip()
    conversation_id = data.get('conversation_id')
    preferred_provider = data.get('provider')
    preferred_model = data.get('model')
    
    # Validate question
    is_valid, error_msg = validate_question_length(question)
    if not is_valid:
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400
    
    try:
        # Add user message to conversation
        conversation_manager.add_user_message(conversation_id, question)
        
        # Get database path from app config
        db_path = current_app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        print(f"🔍 Using database path: {db_path}")
        
        # Create query engine and process question
        query_engine = create_query_engine(db_path)
        
        # Process the question asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                query_engine.process_question(
                    question, admin_email, preferred_provider, preferred_model
                )
            )
        finally:
            loop.close()
        
        if result['success']:
            # Format response message
            response_content = f"Found {result.get('row_count', 0)} results"
            if result.get('chart_suggestion'):
                response_content += " with chart visualization available"
            
            # Add assistant message
            conversation_manager.add_assistant_message(
                conversation_id=conversation_id,
                content=response_content,
                sql_query=result.get('sql'),
                query_result=str(result.get('columns', [])) + str(result.get('rows', [])),
                ai_provider=result.get('ai_provider'),
                ai_model=result.get('ai_model'),
                tokens_used=result.get('tokens_used', 0),
                cost_cents=result.get('cost_cents', 0),
                response_time_ms=result.get('processing_time_ms', 0)
            )
            
            return jsonify({
                'success': True,
                'question': question,
                'sql': result.get('sql'),
                'columns': result.get('columns', []),
                'rows': result.get('rows', []),
                'row_count': result.get('row_count', 0),
                'chart_suggestion': result.get('chart_suggestion'),
                'ai_provider': result.get('ai_provider'),
                'ai_model': result.get('ai_model'),
                'processing_time_ms': result.get('processing_time_ms', 0)
            })
        else:
            # Add error message
            conversation_manager.add_error_message(conversation_id, result.get('error', 'Unknown error'))
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Query processing failed'),
                'question': question
            }), 400
    
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
            conversation_list.append(stats)
        
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