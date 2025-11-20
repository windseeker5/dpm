"""
Gemini AI Analytics Chatbot Routes
Uses analytics_chatbot_simple.html template (the modern, clean UI)
"""
import json
import asyncio
import re
import traceback
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from datetime import datetime
import os

from .providers.gemini import create_gemini_provider
from .config import GOOGLE_AI_API_KEY, CHATBOT_ENABLE_GEMINI
from .query_engine import create_query_engine
from .ai_providers import AIRequest

# Create the blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# Greeting patterns
GREETING_PATTERNS = [
    r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b',
    r'\b(thanks|thank you|appreciate)\b',
    r'\b(bye|goodbye|see you|farewell)\b',
    r'^(how are you|what\'s up|sup)\b',
    r'^(help|what can you do)\b',
]


def is_greeting_or_conversation(question: str) -> bool:
    """Check if the question is a greeting or conversational (not a data query)"""
    question_lower = question.lower().strip()

    # Check against greeting patterns
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, question_lower, re.IGNORECASE):
            return True

    # Check if question is very short (likely conversational)
    if len(question_lower.split()) <= 3 and not any(word in question_lower for word in ['show', 'get', 'find', 'list', 'count', 'total', 'how many']):
        return True

    return False


async def get_conversational_response(question: str, provider) -> str:
    """Get a natural conversational response from Gemini"""
    system_prompt = """You are a helpful AI assistant for Minipass, a platform that helps manage activities, users, and revenue.

When users greet you or ask conversational questions:
- Respond naturally and professionally
- Remind them you can help analyze their data about users, activities, revenue, signups, and passports
- Keep responses brief (1-2 sentences)
- Be friendly and encouraging

Examples:
User: "Hello"
You: "Hi! I'm your Minipass AI assistant. I can help you analyze your data - ask me about your users, revenue, activities, or any insights you need!"

User: "Thanks"
You: "You're welcome! Feel free to ask me anything about your data anytime."

User: "What can you do?"
You: "I can help you analyze your Minipass data! Ask me about your revenue, user signups, activity performance, or any metrics you'd like to see."
"""

    ai_request = AIRequest(
        prompt=question,
        system_prompt=system_prompt,
        model='gemini-2.0-flash-exp',  # Use 2.0 Flash Exp for higher rate limits
        temperature=0.7,  # Higher temperature for natural conversation
        max_tokens=150
    )

    response = await provider.generate(ai_request)
    return response.content if response.content else "Hello! I'm here to help you analyze your Minipass data. What would you like to know?"


def get_gemini_provider():
    """Get configured Gemini provider"""
    if not CHATBOT_ENABLE_GEMINI or not GOOGLE_AI_API_KEY:
        return None

    try:
        provider = create_gemini_provider(GOOGLE_AI_API_KEY)
        return provider
    except Exception as e:
        current_app.logger.error(f"Failed to create Gemini provider: {e}")
        return None


def check_gemini_availability():
    """Check if Gemini API is available"""
    provider = get_gemini_provider()
    if not provider:
        return False
    return provider.check_availability()


def get_gemini_models():
    """Get available Gemini models"""
    provider = get_gemini_provider()
    if not provider or not provider.check_availability():
        return []

    try:
        models = provider.get_available_models()
        return [{
            "id": model,
            "name": model,
            "available": True
        } for model in models]
    except Exception as e:
        current_app.logger.error(f"Error getting Gemini models: {e}")
        return []


@chatbot_bp.route('/')
def index():
    """Main chatbot interface"""
    # Simple auth check
    admin_email = session.get('admin')
    if not admin_email:
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))

    # Use the CORRECT template - the modern, clean UI
    return render_template(
        'analytics_chatbot_simple.html',
        conversation_id='gemini-' + datetime.now().strftime('%Y%m%d%H%M%S')
    )


@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a user question using Gemini and query engine"""

    # Simple auth check - allow testing for development
    admin_email = session.get('admin')
    if not admin_email:
        current_app.logger.warning("No admin session, allowing for development")
        admin_email = "test@example.com"

    # Get question from request
    if request.content_type and 'application/json' in request.content_type:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    question = data.get('question', '').strip()
    model = data.get('model', 'gemini-2.0-flash-exp')  # Default to Gemini 2.0 Flash Exp (1,500 RPD)

    # FORCE Gemini model if UI sends a non-Gemini model name
    # This ensures we use Gemini as primary provider, not Groq fallback
    if 'gemini' not in model.lower():
        model = 'gemini-2.0-flash-exp'  # Override to Gemini model

    # Basic validation
    if not question:
        return jsonify({
            'success': False,
            'error': 'Question is required'
        }), 400

    if len(question) > 2000:
        return jsonify({
            'success': False,
            'error': 'Question is too long (max 2000 characters)'
        }), 400

    # Check if Gemini is available
    if not check_gemini_availability():
        return jsonify({
            'success': False,
            'error': '⚠️ AI Analytics temporarily unavailable. Please contact Minipass support.'
        }), 503

    try:
        # Check if this is a greeting or conversational question
        if is_greeting_or_conversation(question):
            # Handle conversational questions with Gemini
            provider = get_gemini_provider()
            if not provider:
                return jsonify({
                    'success': False,
                    'error': '⚠️ AI Analytics temporarily unavailable. Please contact Minipass support.'
                }), 503

            # Run async conversational response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            answer = loop.run_until_complete(
                get_conversational_response(question, provider)
            )
            loop.close()

            # Return conversational response
            response = {
                'success': True,
                'question': question,
                'answer': answer,
                'conversational': True,  # Flag to indicate no SQL/data
                'model': model,
                'conversation_id': data.get('conversation_id', 'gemini'),
                'timestamp': datetime.now().isoformat(),
                'provider': 'gemini'
            }
            return jsonify(response)

        # Otherwise, handle as a data query
        # Get database path from Flask config
        db_path = current_app.config.get('DATABASE_PATH', 'instance/minipass.db')
        if not db_path.startswith('/'):
            # Make it absolute path
            import os
            db_path = os.path.join(current_app.root_path, db_path)

        # Create query engine and process question using Gemini
        query_engine = create_query_engine(db_path)

        # Run async query processing - simple and direct
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            query_engine.process_question(
                question,  # Pass raw question directly - trust the AI
                admin_email,
                preferred_provider='gemini',
                preferred_model=model
            )
        )
        loop.close()

        # Log the result for debugging
        current_app.logger.info(f"Query result: {json.dumps(result, indent=2, default=str)}")

        # Add conversation ID to result
        result['conversation_id'] = data.get('conversation_id', 'gemini')

        if result.get('success'):
            # Create natural language answer based on results
            row_count = result.get('row_count', 0)

            if row_count == 0:
                answer = "I didn't find any results for that query. Try asking in a different way or check if the data exists."
            elif row_count == 1:
                answer = "I found 1 result for your question."
            else:
                answer = f"I found {row_count} results for your question."

            # Format response for the simple template
            response = {
                'success': True,
                'question': question,
                'answer': answer,
                'sql': result.get('sql', ''),
                'rows': result.get('rows', []),
                'columns': result.get('columns', []),
                'row_count': row_count,
                'conversational': False,
                'model': result.get('ai_model', model),
                'conversation_id': result.get('conversation_id'),
                'timestamp': datetime.now().isoformat(),
                'provider': 'gemini'
            }
            return jsonify(response)
        else:
            # Log the failed result
            error_msg = result.get('error', 'Failed to process question')
            current_app.logger.error(f"Query processing failed: {error_msg}")
            current_app.logger.error(f"Full result: {json.dumps(result, indent=2, default=str)}")

            return jsonify({
                'success': False,
                'error': f'Query failed: {error_msg}'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Error processing question: {e}")
        current_app.logger.error(f"Full traceback:\n{traceback.format_exc()}")
        current_app.logger.error(f"Question was: {question}")
        current_app.logger.error(f"Model was: {model}")

        # Return detailed error for debugging (temporarily)
        return jsonify({
            'success': False,
            'error': f'Debug Error: {str(e)} - Check Flask logs for details'
        }), 500


@chatbot_bp.route('/status')
def status():
    """Check Gemini API status"""
    gemini_available = check_gemini_availability()

    return jsonify({
        'status': 'online' if gemini_available else 'offline',
        'provider': 'gemini',
        'api_configured': GOOGLE_AI_API_KEY is not None,
        'available': gemini_available,
        'timestamp': datetime.now().isoformat()
    })


@chatbot_bp.route('/models')
def list_models():
    """Get available Gemini models"""
    try:
        # Check if Gemini is available first
        if not check_gemini_availability():
            return jsonify({
                'success': False,
                'error': 'Gemini API is not available',
                'models': [],
                'server_status': 'offline'
            }), 503

        # Get real models from Gemini
        models = get_gemini_models()

        return jsonify({
            'success': True,
            'models': models,
            'server_status': 'online',
            'provider': 'gemini',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"Error getting models: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get models: {str(e)}',
            'models': [],
            'server_status': 'error'
        }), 500


@chatbot_bp.route('/model-status')
def model_status():
    """Model status endpoint for frontend LED indicator"""
    gemini_available = check_gemini_availability()

    if gemini_available:
        # Try to get models to confirm full functionality
        models = get_gemini_models()
        if models:
            return jsonify({
                'status': 'online',
                'model': f'{len(models)} models available',
                'connected': True,
                'models_count': len(models)
            })
        else:
            return jsonify({
                'status': 'partial',
                'model': 'API online, no models',
                'connected': False,
                'models_count': 0
            })
    else:
        return jsonify({
            'status': 'offline',
            'model': 'Gemini API offline',
            'connected': False,
            'models_count': 0
        })


@chatbot_bp.route('/test-connection')
def test_connection():
    """Test endpoint to verify Gemini connection and models"""
    try:
        # Test basic connection
        gemini_available = check_gemini_availability()

        if not gemini_available:
            return jsonify({
                'success': False,
                'error': 'Cannot connect to Gemini API',
                'provider': 'gemini'
            })

        # Get models
        models = get_gemini_models()

        return jsonify({
            'success': True,
            'api_available': True,
            'models_count': len(models),
            'models': [m['id'] for m in models],
            'provider': 'gemini'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}'
        })


# Error handlers
@chatbot_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@chatbot_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
