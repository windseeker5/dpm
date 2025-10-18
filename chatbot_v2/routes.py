"""
Flask routes for the AI Analytics Chatbot
"""
import asyncio
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
# from flask_wtf.csrf import exempt  # Not needed for now

# Import all necessary modules
from .ai_providers import provider_manager
from .providers.ollama import create_ollama_provider
from .providers.gemini import create_gemini_provider
from .query_engine import create_query_engine
from .conversation import conversation_manager
from .utils import get_current_admin_email, validate_question_length
from .config import (
    OLLAMA_BASE_URL,
    CHATBOT_ENABLE_OLLAMA,
    CHATBOT_ENABLE_GEMINI,
    GOOGLE_AI_API_KEY
)


# Create the blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


def initialize_chatbot():
    """Initialize AI providers"""

    # Try Gemini as primary provider if enabled
    if CHATBOT_ENABLE_GEMINI and GOOGLE_AI_API_KEY:
        try:
            gemini_provider = create_gemini_provider(GOOGLE_AI_API_KEY)
            # Check if Gemini is actually available
            if gemini_provider.check_availability():
                models = gemini_provider.get_available_models()
                if models:
                    provider_manager.register_provider(gemini_provider, is_primary=True)
                    print(f"✅ Gemini provider registered as primary with {len(models)} models")
                    print(f"   Available models: {', '.join(models)}")
                else:
                    print("⚠️ Gemini provider has no models available")
            else:
                print("⚠️ Gemini API not reachable")
        except Exception as e:
            print(f"❌ Gemini not available: {e}")
    elif CHATBOT_ENABLE_GEMINI:
        print("⚠️ Gemini enabled but GOOGLE_AI_API_KEY not configured")

    # If no primary provider is set, show error
    if provider_manager.primary_provider is None:
        print("❌ No AI provider available! Please configure GOOGLE_AI_API_KEY.")
        print("   Get your API key from: https://ai.google.dev/aistudio")

# Initialize chatbot when module is imported
initialize_chatbot()


@chatbot_bp.route('/')
def index():
    """Main chatbot interface"""
    
    # Simplified auth check
    admin_email = session.get('admin')
    if not admin_email:
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))
    
    # Get available Gemini models
    available_models = []
    provider_status = {'gemini': {'available': False, 'models': []}}

    # Check Gemini models
    if CHATBOT_ENABLE_GEMINI and GOOGLE_AI_API_KEY:
        try:
            gemini_provider = create_gemini_provider(GOOGLE_AI_API_KEY)
            if gemini_provider.check_availability():
                models = gemini_provider.get_available_models()
                provider_status['gemini']['available'] = True
                provider_status['gemini']['models'] = models

                for model in models:
                    # Clean up model names for display
                    display_name = model.replace('gemini-', '').replace('-', ' ').title()
                    available_models.append({
                        'provider': 'gemini',
                        'model': model,
                        'display_name': f"Gemini {display_name}",
                        'description': f'Google Gemini: {display_name}'
                    })
            else:
                print("Gemini API not available for model listing")
        except Exception as e:
            print(f"Failed to get Gemini models: {e}")
    else:
        print("⚠️ Gemini not configured. Set GOOGLE_AI_API_KEY environment variable.")

    # Fallback message if no models available
    if not available_models:
        available_models = [{
            'provider': 'none',
            'model': 'none',
            'display_name': 'AI Analytics Unavailable',
            'description': 'Please contact Minipass support - API key not configured'
        }]
    
    messages = []
    conversation_id = 'test-conversation'
    
    return render_template(
        'analytics_chatbot_modern.html',
        messages=messages,
        conversation_id=conversation_id,
        session_token='test-session',
        available_models=available_models,
        provider_status=provider_status,
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
    preferred_provider = data.get('provider', 'gemini')
    preferred_model = data.get('model', 'gemini-1.5-flash')
    
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
        # Use query engine to process question with Gemini
        print(f"💬 Processing question with {preferred_provider}/{preferred_model}: {question}")

        # Validate model selection for Gemini
        if preferred_provider == 'gemini':
            if not (CHATBOT_ENABLE_GEMINI and GOOGLE_AI_API_KEY):
                return jsonify({
                    'success': False,
                    'error': '⚠️ AI Analytics temporarily unavailable. Please contact Minipass support.',
                    'conversation_id': conversation_id
                }), 503

            try:
                gemini_provider = create_gemini_provider(GOOGLE_AI_API_KEY)
                if not gemini_provider.check_availability():
                    return jsonify({
                        'success': False,
                        'error': '⚠️ AI Analytics temporarily unavailable. Please contact Minipass support.',
                        'conversation_id': conversation_id
                    }), 503
                else:
                    available_models = gemini_provider.get_available_models()
                    if preferred_model not in available_models:
                        print(f"⚠️ Model {preferred_model} not found, using first available")
                        # Use first available preferred model
                        from .config import PREFERRED_MODELS
                        for model in PREFERRED_MODELS:
                            if model in available_models:
                                preferred_model = model
                                break
                        else:
                            preferred_model = available_models[0] if available_models else 'gemini-1.5-flash'
            except Exception as e:
                print(f"❌ Gemini validation failed: {e}")
                return jsonify({
                    'success': False,
                    'error': '⚠️ AI Analytics temporarily unavailable. Please contact Minipass support.',
                    'conversation_id': conversation_id
                }), 503
        
        # Get database path from Flask config
        db_path = current_app.config.get('DATABASE_PATH', 'instance/minipass.db')
        if not db_path.startswith('/'):
            # Make it absolute path
            import os
            db_path = os.path.join(current_app.root_path, db_path)
        
        # Create query engine and process question
        query_engine = create_query_engine(db_path)
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            query_engine.process_question(
                question, 
                admin_email, 
                preferred_provider=preferred_provider,
                preferred_model=preferred_model
            )
        )
        loop.close()
        
        # Add conversation ID to result
        result['conversation_id'] = conversation_id
        
        print(f"✅ Query engine result: {result.get('success', False)}")
        if result.get('success'):
            print(f"   SQL: {result.get('sql', 'N/A')}")
            print(f"   Rows: {result.get('row_count', 0)}")
            print(f"   Provider: {result.get('ai_provider', 'N/A')}")
            print(f"   Model: {result.get('ai_model', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
    
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
    
    # Simplified auth for status check
    admin_email = session.get('admin')
    if not admin_email:
        admin_email = "test@example.com"  # Allow status check without strict auth
    
    # Get provider manager status
    status = provider_manager.get_all_status()

    # Add additional Gemini connection details
    if CHATBOT_ENABLE_GEMINI and GOOGLE_AI_API_KEY:
        try:
            gemini_provider = create_gemini_provider(GOOGLE_AI_API_KEY)
            gemini_available = gemini_provider.check_availability()
            gemini_models = gemini_provider.get_available_models() if gemini_available else []

            status['gemini_direct'] = {
                'api_configured': True,
                'available': gemini_available,
                'models': gemini_models,
                'model_count': len(gemini_models)
            }
        except Exception as e:
            status['gemini_direct'] = {
                'api_configured': True,
                'available': False,
                'error': str(e),
                'models': []
            }
    else:
        status['gemini_direct'] = {
            'api_configured': False,
            'available': False,
            'error': 'GOOGLE_AI_API_KEY not configured',
            'models': []
        }

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


@chatbot_bp.route('/check-model', methods=['POST'])
def check_model():
    """Check if a specific model is available"""
    
    # Simplified auth check
    admin_email = session.get('admin')
    if not admin_email:
        return jsonify({'error': 'Authentication required'}), 401
    
    model = request.form.get('model')
    if not model:
        return jsonify({
            'success': False,
            'error': 'Model parameter required'
        }), 400
    
    try:
        # Check Gemini models
        if CHATBOT_ENABLE_GEMINI and GOOGLE_AI_API_KEY:
            gemini_provider = create_gemini_provider(GOOGLE_AI_API_KEY)

            if gemini_provider.check_availability():
                available_models = gemini_provider.get_available_models()
                is_available = model in available_models

                return jsonify({
                    'success': True,
                    'available': is_available,
                    'model': model
                })
            else:
                return jsonify({
                    'success': True,
                    'available': False,
                    'model': model,
                    'error': 'Gemini API not available'
                })
        else:
            return jsonify({
                'success': True,
                'available': False,
                'model': model,
                'error': 'Gemini API key not configured'
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