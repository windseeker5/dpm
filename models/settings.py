# models/settings.py - Enhanced Settings Models
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import json
import enum
from cryptography.fernet import Fernet
import os

from models import db

class SettingType(enum.Enum):
    """Setting types for validation and UI rendering"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    EMAIL = "email"
    URL = "url"
    PASSWORD = "password"
    JSON = "json"
    TEXT = "text"

class SettingScope(enum.Enum):
    """Setting scopes for organization and access control"""
    SYSTEM = "system"          # Core system settings
    EMAIL = "email"            # Email configuration
    ORGANIZATION = "organization"  # Org details
    SECURITY = "security"      # Security settings
    INTEGRATION = "integration"   # Third-party integrations
    UI = "ui"                  # UI customization
    FEATURE = "feature"        # Feature flags

class SettingSchema(db.Model):
    """Schema definition for settings - defines what settings are available"""
    __tablename__ = 'setting_schemas'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(SettingType), nullable=False)
    scope = Column(SQLEnum(SettingScope), nullable=False)
    default_value = Column(Text)
    validation_rules = Column(JSON)  # JSON field for validation rules
    is_sensitive = Column(Boolean, default=False)  # Encrypt sensitive values
    is_required = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)  # Can be accessed by non-admin users
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<SettingSchema {self.key}>'

class SettingValue(db.Model):
    """Actual setting values with audit trail"""
    __tablename__ = 'setting_values'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text)
    encrypted_value = Column(Text)  # For sensitive settings
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(255))
    updated_by = Column(String(255))
    
    def __repr__(self):
        return f'<SettingValue {self.key}>'
    
    @property
    def decrypted_value(self):
        """Get decrypted value for sensitive settings"""
        if self.encrypted_value:
            return self._decrypt_value(self.encrypted_value)
        return self.value
    
    @decrypted_value.setter
    def decrypted_value(self, value):
        """Set encrypted value for sensitive settings"""
        schema = SettingSchema.query.filter_by(key=self.key).first()
        if schema and schema.is_sensitive:
            self.encrypted_value = self._encrypt_value(value)
            self.value = None
        else:
            self.value = value
            self.encrypted_value = None
    
    def _encrypt_value(self, value):
        """Encrypt sensitive values"""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()
    
    def _decrypt_value(self, encrypted_value):
        """Decrypt sensitive values"""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    
    def _get_encryption_key(self):
        """Get or create encryption key"""
        key = os.environ.get('MINIPASS_ENCRYPTION_KEY')
        if not key:
            # Generate a key if none exists (should be set in production)
            key = Fernet.generate_key().decode()
            print(f"WARNING: Generated new encryption key. Set MINIPASS_ENCRYPTION_KEY={key}")
        return key.encode() if isinstance(key, str) else key

class SettingChangeLog(db.Model):
    """Audit trail for setting changes"""
    __tablename__ = 'setting_change_logs'
    
    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), nullable=False, index=True)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String(255))
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    change_reason = Column(String(500))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    def __repr__(self):
        return f'<SettingChangeLog {self.setting_key} at {self.changed_at}>'

# ============================================================================
# SETTINGS MANAGER CLASS
# ============================================================================

class SettingsManager:
    """High-level settings management with validation and caching"""
    
    _cache = {}
    _cache_timestamp = None
    _cache_ttl = 300  # 5 minutes
    
    @classmethod
    def get(cls, key, default=None):
        """Get setting value with caching"""
        # Check cache first
        if cls._is_cache_valid():
            if key in cls._cache:
                return cls._cache[key]
        
        # Get from database
        setting_value = SettingValue.query.filter_by(key=key).first()
        if setting_value:
            value = setting_value.decrypted_value
            cls._cache[key] = value
            return value
        
        # Get default from schema
        schema = SettingSchema.query.filter_by(key=key).first()
        if schema and schema.default_value:
            return schema.default_value
        
        return default
    
    @classmethod
    def set(cls, key, value, changed_by=None, change_reason=None, request_info=None):
        """Set setting value with validation and audit trail"""
        # Validate against schema
        schema = SettingSchema.query.filter_by(key=key).first()
        if not schema:
            raise ValueError(f"Setting '{key}' is not defined in schema")
        
        # Validate value
        validated_value = cls._validate_value(value, schema)
        
        # Get current value for audit trail
        current_setting = SettingValue.query.filter_by(key=key).first()
        old_value = current_setting.decrypted_value if current_setting else None
        
        # Create or update setting
        if current_setting:
            current_setting.decrypted_value = validated_value
            current_setting.updated_by = changed_by
            current_setting.updated_at = datetime.now(timezone.utc)
        else:
            current_setting = SettingValue(
                key=key,
                created_by=changed_by,
                updated_by=changed_by
            )
            current_setting.decrypted_value = validated_value
            db.session.add(current_setting)
        
        # Create audit log
        if old_value != validated_value:
            change_log = SettingChangeLog(
                setting_key=key,
                old_value=old_value,
                new_value=validated_value if not schema.is_sensitive else '[ENCRYPTED]',
                changed_by=changed_by,
                change_reason=change_reason,
                ip_address=request_info.get('ip') if request_info else None,
                user_agent=request_info.get('user_agent') if request_info else None
            )
            db.session.add(change_log)
        
        # Update cache
        cls._cache[key] = validated_value
        
        return validated_value
    
    @classmethod
    def get_by_scope(cls, scope):
        """Get all settings for a specific scope"""
        schemas = SettingSchema.query.filter_by(scope=scope).all()
        result = {}
        
        for schema in schemas:
            value = cls.get(schema.key, schema.default_value)
            result[schema.key] = {
                'value': value,
                'schema': {
                    'name': schema.name,
                    'description': schema.description,
                    'type': schema.type.value,
                    'is_required': schema.is_required,
                    'is_sensitive': schema.is_sensitive,
                    'validation_rules': schema.validation_rules
                }
            }
        
        return result
    
    @classmethod
    def get_public_settings(cls):
        """Get settings that are safe to expose to frontend"""
        schemas = SettingSchema.query.filter_by(is_public=True).all()
        result = {}
        
        for schema in schemas:
            result[schema.key] = cls.get(schema.key, schema.default_value)
        
        return result
    
    @classmethod
    def validate_all(cls):
        """Validate all current settings against their schemas"""
        errors = []
        
        for setting_value in SettingValue.query.all():
            schema = SettingSchema.query.filter_by(key=setting_value.key).first()
            if schema:
                try:
                    cls._validate_value(setting_value.decrypted_value, schema)
                except ValueError as e:
                    errors.append(f"{setting_value.key}: {str(e)}")
        
        return errors
    
    @classmethod
    def export_settings(cls, include_sensitive=False):
        """Export all settings for backup"""
        result = {}
        
        for setting_value in SettingValue.query.all():
            schema = SettingSchema.query.filter_by(key=setting_value.key).first()
            
            if schema and schema.is_sensitive and not include_sensitive:
                result[setting_value.key] = '[REDACTED]'
            else:
                result[setting_value.key] = setting_value.decrypted_value
        
        return result
    
    @classmethod
    def import_settings(cls, settings_data, imported_by=None, overwrite=False):
        """Import settings from backup"""
        imported_count = 0
        errors = []
        
        for key, value in settings_data.items():
            if key.startswith('_'):  # Skip metadata keys
                continue
            
            try:
                # Check if setting exists
                existing = SettingValue.query.filter_by(key=key).first()
                if existing and not overwrite:
                    continue
                
                cls.set(key, value, changed_by=imported_by, change_reason="Import from backup")
                imported_count += 1
                
            except Exception as e:
                errors.append(f"{key}: {str(e)}")
        
        return imported_count, errors
    
    @classmethod
    def _validate_value(cls, value, schema):
        """Validate a value against its schema"""
        if value is None:
            if schema.is_required:
                raise ValueError("Value is required")
            return None
        
        # Type validation
        if schema.type == SettingType.INTEGER:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError("Value must be an integer")
        
        elif schema.type == SettingType.FLOAT:
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError("Value must be a number")
        
        elif schema.type == SettingType.BOOLEAN:
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = bool(value)
        
        elif schema.type == SettingType.EMAIL:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                raise ValueError("Value must be a valid email address")
        
        elif schema.type == SettingType.URL:
            import re
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, str(value)):
                raise ValueError("Value must be a valid URL")
        
        elif schema.type == SettingType.JSON:
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    raise ValueError("Value must be valid JSON")
        
        # Custom validation rules
        if schema.validation_rules:
            cls._apply_validation_rules(value, schema.validation_rules)
        
        return value
    
    @classmethod
    def _apply_validation_rules(cls, value, rules):
        """Apply custom validation rules"""
        if 'min_length' in rules:
            if len(str(value)) < rules['min_length']:
                raise ValueError(f"Value must be at least {rules['min_length']} characters")
        
        if 'max_length' in rules:
            if len(str(value)) > rules['max_length']:
                raise ValueError(f"Value must be no more than {rules['max_length']} characters")
        
        if 'min_value' in rules:
            if float(value) < rules['min_value']:
                raise ValueError(f"Value must be at least {rules['min_value']}")
        
        if 'max_value' in rules:
            if float(value) > rules['max_value']:
                raise ValueError(f"Value must be no more than {rules['max_value']}")
        
        if 'pattern' in rules:
            import re
            if not re.match(rules['pattern'], str(value)):
                raise ValueError(f"Value does not match required pattern")
        
        if 'allowed_values' in rules:
            if value not in rules['allowed_values']:
                raise ValueError(f"Value must be one of: {', '.join(rules['allowed_values'])}")
    
    @classmethod
    def _is_cache_valid(cls):
        """Check if cache is still valid"""
        if cls._cache_timestamp is None:
            return False
        
        return (datetime.now(timezone.utc) - cls._cache_timestamp).seconds < cls._cache_ttl
    
    @classmethod
    def clear_cache(cls):
        """Clear the settings cache"""
        cls._cache = {}
        cls._cache_timestamp = None

# ============================================================================
# INITIALIZATION DATA
# ============================================================================

def initialize_setting_schemas():
    """Initialize default setting schemas"""
    schemas = [
        # Email Configuration
        {
            'key': 'MAIL_SERVER',
            'name': 'Mail Server',
            'description': 'SMTP server hostname',
            'type': SettingType.STRING,
            'scope': SettingScope.EMAIL,
            'is_required': True,
            'validation_rules': {'min_length': 1}
        },
        {
            'key': 'MAIL_PORT',
            'name': 'Mail Port',
            'description': 'SMTP server port',
            'type': SettingType.INTEGER,
            'scope': SettingScope.EMAIL,
            'default_value': '587',
            'validation_rules': {'min_value': 1, 'max_value': 65535}
        },
        {
            'key': 'MAIL_USE_TLS',
            'name': 'Use TLS',
            'description': 'Enable TLS encryption for email',
            'type': SettingType.BOOLEAN,
            'scope': SettingScope.EMAIL,
            'default_value': 'True'
        },
        {
            'key': 'MAIL_USERNAME',
            'name': 'Mail Username',
            'description': 'SMTP username',
            'type': SettingType.STRING,
            'scope': SettingScope.EMAIL
        },
        {
            'key': 'MAIL_PASSWORD',
            'name': 'Mail Password',
            'description': 'SMTP password',
            'type': SettingType.PASSWORD,
            'scope': SettingScope.EMAIL,
            'is_sensitive': True
        },
        {
            'key': 'MAIL_DEFAULT_SENDER',
            'name': 'Default Sender',
            'description': 'Default email sender address',
            'type': SettingType.EMAIL,
            'scope': SettingScope.EMAIL
        },
        {
            'key': 'MAIL_SENDER_NAME',
            'name': 'Sender Name',
            'description': 'Display name for email sender (e.g., LHGI, Your Organization)',
            'type': SettingType.STRING,
            'scope': SettingScope.EMAIL,
            'default_value': 'Minipass',
            'validation_rules': {'max_length': 100}
        },
        
        # Organization Settings
        {
            'key': 'ORG_NAME',
            'name': 'Organization Name',
            'description': 'Name of your organization',
            'type': SettingType.STRING,
            'scope': SettingScope.ORGANIZATION,
            'is_public': True,
            'validation_rules': {'max_length': 255}
        },
        {
            'key': 'DEFAULT_PASS_AMOUNT',
            'name': 'Default Pass Amount',
            'description': 'Default price for passes',
            'type': SettingType.FLOAT,
            'scope': SettingScope.ORGANIZATION,
            'default_value': '50',
            'validation_rules': {'min_value': 0}
        },
        {
            'key': 'DEFAULT_SESSION_QT',
            'name': 'Default Session Quantity',
            'description': 'Default number of sessions per pass',
            'type': SettingType.INTEGER,
            'scope': SettingScope.ORGANIZATION,
            'default_value': '4',
            'validation_rules': {'min_value': 1}
        },
        {
            'key': 'CALL_BACK_DAYS',
            'name': 'Callback Days',
            'description': 'Days to wait before callback',
            'type': SettingType.INTEGER,
            'scope': SettingScope.ORGANIZATION,
            'default_value': '0',
            'validation_rules': {'min_value': 0}
        },
        {
            'key': 'LOGO_FILENAME',
            'name': 'Logo Filename',
            'description': 'Organization logo filename',
            'type': SettingType.STRING,
            'scope': SettingScope.ORGANIZATION,
            'is_public': True
        },
        
        # System Settings
        {
            'key': 'ACTIVITY_LIST',
            'name': 'Activity Tags',
            'description': 'Available activity tags',
            'type': SettingType.JSON,
            'scope': SettingScope.SYSTEM,
            'default_value': '[]'
        },
        {
            'key': 'EMAIL_INFO_TEXT',
            'name': 'Email Info Text',
            'description': 'Informational text in emails',
            'type': SettingType.TEXT,
            'scope': SettingScope.EMAIL
        },
        {
            'key': 'EMAIL_FOOTER_TEXT',
            'name': 'Email Footer Text',
            'description': 'Footer text in emails',
            'type': SettingType.TEXT,
            'scope': SettingScope.EMAIL
        },
        
        # Payment Bot Settings
        {
            'key': 'ENABLE_EMAIL_PAYMENT_BOT',
            'name': 'Enable Payment Bot',
            'description': 'Enable automatic payment detection',
            'type': SettingType.BOOLEAN,
            'scope': SettingScope.INTEGRATION,
            'default_value': 'False'
        },
        {
            'key': 'BANK_EMAIL_FROM',
            'name': 'Bank Email From',
            'description': 'Bank notification email address',
            'type': SettingType.EMAIL,
            'scope': SettingScope.INTEGRATION
        },
        {
            'key': 'BANK_EMAIL_SUBJECT',
            'name': 'Bank Email Subject',
            'description': 'Bank notification email subject pattern',
            'type': SettingType.STRING,
            'scope': SettingScope.INTEGRATION
        },
        {
            'key': 'BANK_EMAIL_NAME_CONFIDANCE',
            'name': 'Name Confidence Threshold',
            'description': 'Confidence threshold for name matching',
            'type': SettingType.INTEGER,
            'scope': SettingScope.INTEGRATION,
            'default_value': '85',
            'validation_rules': {'min_value': 0, 'max_value': 100}
        },
        {
            'key': 'GMAIL_LABEL_FOLDER_PROCESSED',
            'name': 'Gmail Processed Label',
            'description': 'Gmail label for processed emails',
            'type': SettingType.STRING,
            'scope': SettingScope.INTEGRATION,
            'default_value': 'InteractProcessed'
        }
    ]
    
    for schema_data in schemas:
        existing = SettingSchema.query.filter_by(key=schema_data['key']).first()
        if not existing:
            schema = SettingSchema(**schema_data)
            db.session.add(schema)
    
    db.session.commit()