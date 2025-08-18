# config/security.py - Security Configuration and Best Practices
import os
import secrets
from datetime import timedelta
from cryptography.fernet import Fernet

class SecurityConfig:
    """Security configuration for the settings system"""
    
    # Session Security
    SESSION_COOKIE_SECURE = True  # Only over HTTPS in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Session timeout
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Password Requirements
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    PASSWORD_HISTORY_COUNT = 5  # Remember last 5 passwords
    
    # Rate Limiting (requests per window)
    RATE_LIMITS = {
        'admin_create': {'requests': 5, 'window': 300},     # 5 admin creations per 5 minutes
        'admin_update': {'requests': 10, 'window': 300},    # 10 admin updates per 5 minutes
        'admin_delete': {'requests': 3, 'window': 300},     # 3 admin deletions per 5 minutes
        'settings_update': {'requests': 20, 'window': 60},  # 20 settings updates per minute
        'backup_create': {'requests': 3, 'window': 300},    # 3 backups per 5 minutes
        'backup_restore': {'requests': 1, 'window': 600},   # 1 restore per 10 minutes
        'email_test': {'requests': 3, 'window': 300},       # 3 email tests per 5 minutes
        'logo_upload': {'requests': 5, 'window': 300},      # 5 logo uploads per 5 minutes
    }
    
    # File Upload Security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_LOGO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    ALLOWED_BACKUP_EXTENSIONS = {'zip'}
    
    # IP Whitelisting (empty means allow all)
    ADMIN_IP_WHITELIST = []
    
    # Audit Logging
    LOG_ALL_ADMIN_ACTIONS = True
    LOG_FAILED_LOGIN_ATTEMPTS = True
    LOG_SENSITIVE_SETTING_ACCESS = True
    
    # Encryption
    ENCRYPTION_ALGORITHM = 'Fernet'  # Symmetric encryption for settings
    
    @classmethod
    def generate_secret_key(cls):
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def generate_encryption_key(cls):
        """Generate a secure encryption key for sensitive settings"""
        return Fernet.generate_key().decode()
    
    @classmethod
    def validate_password(cls, password):
        """Validate password against security requirements"""
        errors = []
        
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters long")
        
        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if cls.REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if cls.REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    @classmethod
    def is_secure_filename(cls, filename):
        """Check if filename is secure"""
        if not filename:
            return False
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check file extension
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in cls.ALLOWED_LOGO_EXTENSIONS or extension in cls.ALLOWED_BACKUP_EXTENSIONS
    
    @classmethod
    def sanitize_filename(cls, filename):
        """Sanitize uploaded filename"""
        import re
        # Remove any non-alphanumeric characters except dots and dashes
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1)
            filename = name[:250] + '.' + ext
        return filename

class AuditLogger:
    """Centralized audit logging for security events"""
    
    @staticmethod
    def log_admin_action(action, admin_email, details=None, ip_address=None, user_agent=None):
        """Log admin actions for audit trail"""
        from models import db, AdminActionLog
        from datetime import datetime, timezone
        
        log_entry = AdminActionLog(
            admin_email=admin_email,
            action=f"SECURITY: {action}",
            timestamp=datetime.now(timezone.utc)
        )
        
        if details:
            log_entry.action += f" - {details}"
        
        db.session.add(log_entry)
        
        # Also log to application logger
        import logging
        logger = logging.getLogger('minipass.security')
        logger.info(f"Admin Action: {admin_email} - {action}", extra={
            'admin_email': admin_email,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details
        })
    
    @staticmethod
    def log_failed_login(email, ip_address, user_agent):
        """Log failed login attempts"""
        import logging
        logger = logging.getLogger('minipass.security')
        logger.warning(f"Failed login attempt: {email}", extra={
            'email': email,
            'ip_address': ip_address,
            'user_agent': user_agent
        })
    
    @staticmethod
    def log_sensitive_access(setting_key, admin_email, action, ip_address=None):
        """Log access to sensitive settings"""
        import logging
        logger = logging.getLogger('minipass.security')
        logger.info(f"Sensitive setting {action}: {setting_key}", extra={
            'setting_key': setting_key,
            'admin_email': admin_email,
            'action': action,
            'ip_address': ip_address
        })

class SecurityMiddleware:
    """Security middleware for the settings API"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Security checks before processing requests"""
        from flask import request, jsonify, session
        
        # Check IP whitelist for admin endpoints
        if request.endpoint and 'settings' in request.endpoint:
            if SecurityConfig.ADMIN_IP_WHITELIST:
                client_ip = request.remote_addr
                if client_ip not in SecurityConfig.ADMIN_IP_WHITELIST:
                    AuditLogger.log_admin_action(
                        'IP_BLOCKED',
                        session.get('admin_email', 'unknown'),
                        f'Access denied from IP: {client_ip}',
                        client_ip,
                        request.headers.get('User-Agent')
                    )
                    return jsonify({
                        'success': False,
                        'error': 'Access denied',
                        'code': 'IP_BLOCKED'
                    }), 403
        
        # Validate content type for JSON endpoints
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.endpoint and 'api' in request.endpoint:
                if request.content_type != 'application/json':
                    return jsonify({
                        'success': False,
                        'error': 'Content-Type must be application/json'
                    }), 400
    
    def after_request(self, response):
        """Security headers after processing requests"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP for admin pages
        if hasattr(response, 'endpoint') and 'admin' in str(response.endpoint):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        
        return response

class EncryptionManager:
    """Manage encryption for sensitive settings"""
    
    def __init__(self):
        self._key = None
    
    @property
    def key(self):
        """Get encryption key"""
        if not self._key:
            key_string = os.environ.get('MINIPASS_ENCRYPTION_KEY')
            if not key_string:
                # Generate and warn about missing key
                key_string = Fernet.generate_key().decode()
                print(f"WARNING: No MINIPASS_ENCRYPTION_KEY set. Generated temporary key: {key_string}")
                print("Set this as an environment variable for production use!")
            
            self._key = key_string.encode() if isinstance(key_string, str) else key_string
        
        return self._key
    
    def encrypt(self, value):
        """Encrypt a value"""
        if not value:
            return None
        
        f = Fernet(self.key)
        return f.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value):
        """Decrypt a value"""
        if not encrypted_value:
            return None
        
        f = Fernet(self.key)
        return f.decrypt(encrypted_value.encode()).decode()
    
    def rotate_key(self, new_key):
        """Rotate encryption key and re-encrypt all sensitive values"""
        from models.settings import SettingValue, SettingSchema
        
        # Get all sensitive settings
        sensitive_schemas = SettingSchema.query.filter_by(is_sensitive=True).all()
        sensitive_keys = [schema.key for schema in sensitive_schemas]
        
        sensitive_values = SettingValue.query.filter(
            SettingValue.key.in_(sensitive_keys)
        ).all()
        
        # Decrypt with old key
        old_key = self._key
        decrypted_values = {}
        
        for setting_value in sensitive_values:
            if setting_value.encrypted_value:
                decrypted_values[setting_value.key] = self.decrypt(setting_value.encrypted_value)
        
        # Set new key
        self._key = new_key.encode() if isinstance(new_key, str) else new_key
        
        # Re-encrypt with new key
        for setting_value in sensitive_values:
            if setting_value.key in decrypted_values:
                setting_value.encrypted_value = self.encrypt(decrypted_values[setting_value.key])
        
        # Save changes
        from models import db
        db.session.commit()
        
        AuditLogger.log_admin_action('ENCRYPTION_KEY_ROTATED', 'system', 
                                   f'Rotated encryption key for {len(decrypted_values)} sensitive settings')

# Global instances
encryption_manager = EncryptionManager()
security_middleware = SecurityMiddleware()

# Security decorator for sensitive operations
def require_elevated_privileges(f):
    """Decorator requiring re-authentication for sensitive operations"""
    from functools import wraps
    from flask import session, jsonify, request
    from datetime import datetime, timezone
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if recent authentication
        last_auth = session.get('last_elevated_auth')
        if last_auth:
            last_auth_time = datetime.fromisoformat(last_auth)
            if (datetime.now(timezone.utc) - last_auth_time).seconds < 300:  # 5 minutes
                return f(*args, **kwargs)
        
        # Require password confirmation
        password = request.json.get('confirm_password') if request.is_json else None
        if not password:
            return jsonify({
                'success': False,
                'error': 'Password confirmation required for this operation',
                'code': 'ELEVATED_AUTH_REQUIRED'
            }), 403
        
        # Verify password
        from models import Admin
        import bcrypt
        
        admin_email = session.get('admin_email')
        admin = Admin.query.filter_by(email=admin_email).first()
        
        if not admin or not bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
            AuditLogger.log_admin_action('ELEVATED_AUTH_FAILED', admin_email, 
                                       'Failed password confirmation for sensitive operation')
            return jsonify({
                'success': False,
                'error': 'Invalid password',
                'code': 'INVALID_PASSWORD'
            }), 403
        
        # Update last authentication time
        session['last_elevated_auth'] = datetime.now(timezone.utc).isoformat()
        
        return f(*args, **kwargs)
    
    return decorated_function