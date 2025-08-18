"""
Real Ollama Flask routes for the AI Analytics Chatbot
Actually connects to Ollama server and uses real models
"""
import json
import requests
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from datetime import datetime
import os

# Create the blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"

def get_real_ollama_models():
    """Get actual models from Ollama server"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get('models', []):
                models.append({
                    "id": model['name'],
                    "name": model['name'], 
                    "size": model.get('size', 0),
                    "modified_at": model.get('modified_at', ''),
                    "available": True
                })
            return models
        else:
            current_app.logger.error(f"Failed to get models from Ollama: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error connecting to Ollama: {e}")
        return []

def check_ollama_availability():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def send_message_to_ollama(message, model_name):
    """Send message to Ollama and get real LLM response"""
    try:
        # Prepare the request payload for Ollama
        payload = {
            "model": model_name,
            "prompt": message,
            "stream": False,  # Get complete response at once
            "options": {
                "temperature": 0.7,
                "num_predict": 1000  # Limit response length
            }
        }
        
        # Send request to Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60  # Give model time to respond
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('response', 'No response from model'), None
        else:
            error_msg = f"Ollama API error: {response.status_code}"
            current_app.logger.error(f"{error_msg} - {response.text}")
            return None, error_msg
            
    except requests.exceptions.Timeout:
        return None, "Request timed out - model may be loading or busy"
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling Ollama API: {e}")
        return None, f"Failed to connect to Ollama: {str(e)}"
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return None, f"Unexpected error: {str(e)}"

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
        conversation_id='ollama-' + datetime.now().strftime('%Y%m%d%H%M%S')
    )

@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a user question and send to real Ollama model"""
    
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
    model = data.get('model', 'llama3.1:8b')  # Default to llama3.1:8b
    
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
    
    # Check if Ollama is available
    if not check_ollama_availability():
        return jsonify({
            'success': False,
            'error': 'Ollama server is not available. Please ensure it is running on localhost:11434'
        }), 503
    
    try:
        # Send question to the real Ollama model
        answer, error = send_message_to_ollama(question, model)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 500
        
        response = {
            'success': True,
            'question': question,
            'answer': answer,
            'model': model,
            'conversation_id': data.get('conversation_id', 'ollama'),
            'timestamp': datetime.now().isoformat(),
            'provider': 'ollama'
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
    """Check Ollama server status"""
    ollama_available = check_ollama_availability()
    
    return jsonify({
        'status': 'online' if ollama_available else 'offline',
        'provider': 'ollama',
        'server_url': OLLAMA_BASE_URL,
        'available': ollama_available,
        'timestamp': datetime.now().isoformat()
    })

@chatbot_bp.route('/models')
def list_models():
    """Get real available models from Ollama server"""
    try:
        # Check if Ollama is available first
        if not check_ollama_availability():
            return jsonify({
                'success': False,
                'error': 'Ollama server is not available',
                'models': [],
                'server_status': 'offline'
            }), 503
        
        # Get real models from Ollama
        models = get_real_ollama_models()
        
        return jsonify({
            'success': True,
            'models': models,
            'server_status': 'online',
            'server_url': OLLAMA_BASE_URL,
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
    ollama_available = check_ollama_availability()
    
    if ollama_available:
        # Try to get at least one model to confirm full functionality
        models = get_real_ollama_models()
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
                'model': 'Server online, no models',
                'connected': False,
                'models_count': 0
            })
    else:
        return jsonify({
            'status': 'offline',
            'model': 'Ollama server offline',
            'connected': False,
            'models_count': 0
        })

@chatbot_bp.route('/test-connection')
def test_connection():
    """Test endpoint to verify Ollama connection and models"""
    try:
        # Test basic connection
        ollama_available = check_ollama_availability()
        
        if not ollama_available:
            return jsonify({
                'success': False,
                'error': 'Cannot connect to Ollama server',
                'server_url': OLLAMA_BASE_URL
            })
        
        # Get models
        models = get_real_ollama_models()
        
        # Test a simple request with the first available model
        if models:
            test_model = models[0]['id']
            test_response, test_error = send_message_to_ollama(
                "Hello, please respond with just 'OK' to confirm you're working.", 
                test_model
            )
            
            return jsonify({
                'success': True,
                'server_available': True,
                'models_count': len(models),
                'models': [m['id'] for m in models],
                'test_model': test_model,
                'test_response': test_response,
                'test_error': test_error
            })
        else:
            return jsonify({
                'success': False,
                'server_available': True,
                'models_count': 0,
                'error': 'No models found on Ollama server'
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