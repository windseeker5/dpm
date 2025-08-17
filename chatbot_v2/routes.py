"""
Flask routes for the AI Analytics Chatbot
"""
import asyncio
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
# from flask_wtf.csrf import exempt  # Not needed for now

# Import all necessary modules
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
    
    # Try Ollama as primary provider if enabled
    if CHATBOT_ENABLE_OLLAMA:
        try:
            ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
            # Check if Ollama is actually available
            if ollama_provider.check_availability():
                models = ollama_provider.get_available_models()
                if models:
                    provider_manager.register_provider(ollama_provider, is_primary=True)
                    print(f"✅ Ollama provider registered as primary with {len(models)} models")
                    print(f"   Available models: {', '.join(models)}")
                else:
                    print("⚠️ Ollama provider has no models available")
            else:
                print("⚠️ Ollama server not reachable")
        except Exception as e:
            print(f"⚠️ Ollama not available: {e}")
    
    # Use database query provider as fallback
    try:
        from .providers.database_query import create_database_query_provider
        db_provider = create_database_query_provider()
        if db_provider.check_availability():
            # Register as secondary if Ollama is primary, otherwise as primary
            is_primary = provider_manager.primary_provider is None
            provider_manager.register_provider(db_provider, is_primary=is_primary)
            status = "primary" if is_primary else "fallback"
            print(f"✅ Database Query provider registered as {status}")
        else:
            print("⚠️ Database not available")
    except Exception as e:
        print(f"❌ Failed to register Database Query provider: {e}")

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
    
    # Get available Ollama models
    available_models = []
    provider_status = {'ollama': {'available': False, 'models': []}, 'database': {'available': False}}
    
    # Check Ollama models
    try:
        from .providers.ollama import create_ollama_provider
        ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
        if ollama_provider.check_availability():
            models = ollama_provider.get_available_models()
            provider_status['ollama']['available'] = True
            provider_status['ollama']['models'] = models
            
            for model in models:
                # Clean up model names for display
                display_name = model.replace(':latest', '').replace(':', ' ').title()
                available_models.append({
                    'provider': 'ollama',
                    'model': model,
                    'display_name': display_name,
                    'description': f'Ollama: {display_name}'
                })
        else:
            print("Ollama server not available for model listing")
    except Exception as e:
        print(f"Failed to get Ollama models: {e}")
    
    # Check database provider
    try:
        from .providers.database_query import create_database_query_provider
        db_provider = create_database_query_provider()
        if db_provider.check_availability():
            provider_status['database']['available'] = True
            available_models.append({
                'provider': 'database', 
                'model': 'database-query', 
                'display_name': 'Database Query',
                'description': 'Direct database analysis (fallback)'
            })
    except Exception as e:
        print(f"Database provider check failed: {e}")
    
    # Fallback to mock data if no models available
    if not available_models:
        available_models = [{
            'provider': 'mock', 
            'model': 'database-query', 
            'display_name': 'Database Query (Default)',
            'description': 'Fallback mode - basic database queries'
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
    preferred_provider = data.get('provider', 'ollama')
    preferred_model = data.get('model', 'dolphin-mistral:latest')
    
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
        # Use query engine to process question with Ollama
        print(f"💬 Processing question with {preferred_provider}/{preferred_model}: {question}")
        
        # Validate model selection for Ollama
        if preferred_provider == 'ollama':
            try:
                ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
                if not ollama_provider.check_availability():
                    print("⚠️ Ollama not available, falling back to database provider")
                    preferred_provider = 'database'
                    preferred_model = 'database-query'
                else:
                    available_models = ollama_provider.get_available_models()
                    if preferred_model not in available_models:
                        print(f"⚠️ Model {preferred_model} not found, using {PREFERRED_MODELS[0]}")
                        # Use first available preferred model
                        from .config import PREFERRED_MODELS
                        for model in PREFERRED_MODELS:
                            if model in available_models:
                                preferred_model = model
                                break
                        else:
                            preferred_model = available_models[0] if available_models else 'dolphin-mistral:latest'
            except Exception as e:
                print(f"⚠️ Ollama validation failed: {e}, falling back")
                preferred_provider = 'database'
                preferred_model = 'database-query'
        
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
    
    # Add additional Ollama connection details
    try:
        from .providers.ollama import create_ollama_provider
        ollama_provider = create_ollama_provider(OLLAMA_BASE_URL)
        ollama_available = ollama_provider.check_availability()
        ollama_models = ollama_provider.get_available_models() if ollama_available else []
        
        status['ollama_direct'] = {
            'base_url': OLLAMA_BASE_URL,
            'available': ollama_available,
            'models': ollama_models,
            'model_count': len(ollama_models)
        }
    except Exception as e:
        status['ollama_direct'] = {
            'base_url': OLLAMA_BASE_URL,
            'available': False,
            'error': str(e),
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
        # Check if it's the database query model
        if model == 'database-query':
            return jsonify({
                'success': True,
                'available': True,
                'model': model
            })
        
        # Check Ollama models
        from .providers.ollama import create_ollama_provider
        ollama_provider = create_ollama_provider()
        
        if ollama_provider.check_availability():
            available_models = ollama_provider.get_available_models()
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
                'error': 'Ollama service not available'
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