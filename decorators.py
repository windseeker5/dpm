# decorators.py - Security and utility decorators
from functools import wraps
from flask import session, jsonify, request, g
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict

# Rate limiting storage (in production, use Redis)
rate_limit_store = defaultdict(list)

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=10, window=60):
    """
    Rate limiting decorator
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create unique key for client (use IP + admin email if available)
            client_id = request.remote_addr
            if 'admin_email' in session:
                client_id += f":{session['admin_email']}"
            
            # Create rate limit key
            endpoint = request.endpoint
            rate_key = f"{client_id}:{endpoint}"
            
            current_time = datetime.now()
            window_start = current_time - timedelta(seconds=window)
            
            # Clean old requests
            rate_limit_store[rate_key] = [
                req_time for req_time in rate_limit_store[rate_key]
                if req_time > window_start
            ]
            
            # Check if rate limit exceeded
            if len(rate_limit_store[rate_key]) >= max_requests:
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': window
                }), 429
            
            # Add current request
            rate_limit_store[rate_key].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json(schema_class):
    """Decorator to validate JSON input against a schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Content-Type must be application/json'
                }), 400
            
            try:
                schema = schema_class()
                validated_data = schema.load(request.json)
                g.validated_data = validated_data
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON data',
                    'details': str(e)
                }), 400
        return decorated_function
    return decorator

def log_api_call(f):
    """Decorator to log API calls for audit purposes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import db, AdminActionLog
        
        admin_email = session.get('admin_email', 'unknown')
        endpoint = request.endpoint
        method = request.method
        
        # Log the API call
        log = AdminActionLog(
            admin_email=admin_email,
            action=f"API Call: {method} {endpoint}",
            timestamp=datetime.now()
        )
        db.session.add(log)
        
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            raise
    
    return decorated_function

def cache_response(timeout=300):
    """
    Simple response caching decorator
    Args:
        timeout: Cache timeout in seconds
    """
    cache_store = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key
            cache_key = f"{request.endpoint}:{request.args.to_dict()}"
            current_time = datetime.now()
            
            # Check if cached response exists and is valid
            if cache_key in cache_store:
                cached_data, cached_time = cache_store[cache_key]
                if current_time - cached_time < timedelta(seconds=timeout):
                    return cached_data
            
            # Generate new response
            result = f(*args, **kwargs)
            
            # Cache successful responses only
            if hasattr(result, 'status_code') and result.status_code == 200:
                cache_store[cache_key] = (result, current_time)
            
            return result
        return decorated_function
    return decorator