# api/settings.py - RESTful Settings API
from flask import Blueprint, request, jsonify, session
from flask_wtf.csrf import validate_csrf
from marshmallow import Schema, fields, ValidationError, validate
from sqlalchemy.exc import IntegrityError
import bcrypt
import os
import json
from datetime import datetime, timezone

from models import db, Admin, Setting, AdminActionLog
from utils import get_setting, save_setting
from decorators import admin_required, rate_limit

settings_api = Blueprint('settings_api', __name__, url_prefix='/api/v1/settings')

# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================

class AdminSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(validate=validate.Length(min=8), allow_none=True)

class EmailConfigSchema(Schema):
    mail_server = fields.Str(required=True, validate=validate.Length(min=1))
    mail_port = fields.Int(validate=validate.Range(min=1, max=65535))
    mail_use_tls = fields.Bool()
    mail_username = fields.Str()
    mail_password = fields.Str(allow_none=True)
    mail_default_sender = fields.Email()

class OrganizationSchema(Schema):
    org_name = fields.Str(validate=validate.Length(max=255))
    default_pass_amount = fields.Float(validate=validate.Range(min=0))
    default_session_qt = fields.Int(validate=validate.Range(min=1))
    call_back_days = fields.Int(validate=validate.Range(min=0))

class EmailTemplateSchema(Schema):
    subject = fields.Str(validate=validate.Length(max=255))
    title = fields.Str(validate=validate.Length(max=255))
    intro = fields.Str()
    conclusion = fields.Str()
    theme = fields.Str(validate=validate.OneOf(['primary', 'success', 'warning', 'danger']))

class PaymentBotSchema(Schema):
    enable_email_payment_bot = fields.Bool()
    bank_email_from = fields.Email()
    bank_email_subject = fields.Str()
    bank_email_name_confidence = fields.Int(validate=validate.Range(min=0, max=100))
    gmail_label_folder_processed = fields.Str()

# ============================================================================
# ADMIN MANAGEMENT ENDPOINTS
# ============================================================================

@settings_api.route('/admin', methods=['GET'])
@admin_required
def get_admins():
    """Get list of all admin accounts (without passwords)"""
    try:
        admins = Admin.query.all()
        return jsonify({
            'success': True,
            'data': [{'id': admin.id, 'email': admin.email} for admin in admins]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/admin', methods=['POST'])
@admin_required
@rate_limit(max_requests=10, window=60)  # 10 requests per minute
def create_admin():
    """Create new admin account"""
    try:
        schema = AdminSchema()
        data = schema.load(request.json)
        
        # Check if admin already exists
        existing = Admin.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({'success': False, 'error': 'Admin already exists'}), 409
        
        # Hash password
        if not data.get('password'):
            return jsonify({'success': False, 'error': 'Password required'}), 400
            
        password_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
        
        # Create admin
        admin = Admin(email=data['email'], password_hash=password_hash)
        db.session.add(admin)
        
        # Log action
        log_admin_action(f"Created admin: {data['email']}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'id': admin.id, 'email': admin.email}
        }), 201
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/admin/<int:admin_id>', methods=['PUT'])
@admin_required
@rate_limit(max_requests=10, window=60)
def update_admin(admin_id):
    """Update admin account"""
    try:
        admin = Admin.query.get_or_404(admin_id)
        schema = AdminSchema()
        data = schema.load(request.json, partial=True)
        
        # Update email if provided
        if 'email' in data:
            # Check if new email conflicts with existing admin
            existing = Admin.query.filter_by(email=data['email']).first()
            if existing and existing.id != admin_id:
                return jsonify({'success': False, 'error': 'Email already in use'}), 409
            admin.email = data['email']
        
        # Update password if provided
        if data.get('password'):
            admin.password_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
        
        log_admin_action(f"Updated admin: {admin.email}")
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'id': admin.id, 'email': admin.email}
        })
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/admin/<int:admin_id>', methods=['DELETE'])
@admin_required
@rate_limit(max_requests=5, window=60)
def delete_admin(admin_id):
    """Delete admin account"""
    try:
        admin = Admin.query.get_or_404(admin_id)
        
        # Prevent deleting the last admin
        admin_count = Admin.query.count()
        if admin_count <= 1:
            return jsonify({'success': False, 'error': 'Cannot delete the last admin'}), 400
        
        # Prevent self-deletion
        current_admin_email = session.get('admin_email')
        if admin.email == current_admin_email:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        email = admin.email
        db.session.delete(admin)
        log_admin_action(f"Deleted admin: {email}")
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Admin {email} deleted'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# EMAIL CONFIGURATION ENDPOINTS
# ============================================================================

@settings_api.route('/email/config', methods=['GET'])
@admin_required
def get_email_config():
    """Get email SMTP configuration"""
    try:
        config = {
            'mail_server': get_setting('MAIL_SERVER'),
            'mail_port': int(get_setting('MAIL_PORT', '587')),
            'mail_use_tls': get_setting('MAIL_USE_TLS', 'True') == 'True',
            'mail_username': get_setting('MAIL_USERNAME'),
            'mail_default_sender': get_setting('MAIL_DEFAULT_SENDER'),
            # Don't return password for security
        }
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/email/config', methods=['PUT'])
@admin_required
@rate_limit(max_requests=10, window=60)
def update_email_config():
    """Update email SMTP configuration"""
    try:
        schema = EmailConfigSchema()
        data = schema.load(request.json, partial=True)
        
        # Update settings
        for key, value in data.items():
            if key == 'mail_password' and value == '********':
                continue  # Skip masked password
            setting_key = key.upper()
            save_setting(setting_key, str(value))
        
        log_admin_action("Updated email configuration")
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Email configuration updated'})
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/email/test', methods=['POST'])
@admin_required
@rate_limit(max_requests=3, window=300)  # 3 tests per 5 minutes
def test_email_config():
    """Test email configuration by sending a test email"""
    try:
        from utils import send_email_async
        
        test_email = request.json.get('test_email')
        if not test_email:
            return jsonify({'success': False, 'error': 'Test email address required'}), 400
        
        # Send test email asynchronously
        send_email_async(
            to_email=test_email,
            subject="Minipass Email Test",
            template_name="email_test",
            template_vars={
                'org_name': get_setting('ORG_NAME', 'Minipass'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        )
        
        log_admin_action(f"Sent test email to: {test_email}")
        
        return jsonify({'success': True, 'message': 'Test email sent successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# EMAIL TEMPLATES ENDPOINTS
# ============================================================================

@settings_api.route('/email/templates', methods=['GET'])
@admin_required
def get_email_templates():
    """Get all email template configurations"""
    try:
        events = ["pass_created", "pass_redeemed", "payment_received", "payment_late", "signup", "survey_invitation"]
        templates = {}
        
        for event in events:
            templates[event] = {
                'subject': get_setting(f'SUBJECT_{event}'),
                'title': get_setting(f'TITLE_{event}'),
                'intro': get_setting(f'INTRO_{event}'),
                'conclusion': get_setting(f'CONCLUSION_{event}'),
                'theme': get_setting(f'THEME_{event}', 'primary')
            }
        
        return jsonify({'success': True, 'data': templates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/email/templates/<event>', methods=['PUT'])
@admin_required
@rate_limit(max_requests=20, window=60)
def update_email_template(event):
    """Update email template for specific event"""
    try:
        valid_events = ["pass_created", "pass_redeemed", "payment_received", "payment_late", "signup", "survey_invitation"]
        if event not in valid_events:
            return jsonify({'success': False, 'error': 'Invalid event type'}), 400
        
        schema = EmailTemplateSchema()
        data = schema.load(request.json, partial=True)
        
        # Update template settings
        for key, value in data.items():
            setting_key = f"{key.upper()}_{event}"
            save_setting(setting_key, value)
        
        log_admin_action(f"Updated email template: {event}")
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Template for {event} updated'})
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ORGANIZATION SETTINGS ENDPOINTS
# ============================================================================

@settings_api.route('/organization', methods=['GET'])
@admin_required
def get_organization_settings():
    """Get organization settings"""
    try:
        settings = {
            'org_name': get_setting('ORG_NAME'),
            'default_pass_amount': float(get_setting('DEFAULT_PASS_AMOUNT', '50')),
            'default_session_qt': int(get_setting('DEFAULT_SESSION_QT', '4')),
            'call_back_days': int(get_setting('CALL_BACK_DAYS', '0')),
            'email_info_text': get_setting('EMAIL_INFO_TEXT'),
            'email_footer_text': get_setting('EMAIL_FOOTER_TEXT'),
            'logo_filename': get_setting('LOGO_FILENAME')
        }
        return jsonify({'success': True, 'data': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/organization', methods=['PUT'])
@admin_required
@rate_limit(max_requests=10, window=60)
def update_organization_settings():
    """Update organization settings"""
    try:
        schema = OrganizationSchema()
        data = schema.load(request.json, partial=True)
        
        # Map fields to setting keys
        setting_mappings = {
            'org_name': 'ORG_NAME',
            'default_pass_amount': 'DEFAULT_PASS_AMOUNT',
            'default_session_qt': 'DEFAULT_SESSION_QT',
            'call_back_days': 'CALL_BACK_DAYS',
            'email_info_text': 'EMAIL_INFO_TEXT',
            'email_footer_text': 'EMAIL_FOOTER_TEXT'
        }
        
        # Update settings
        for field, value in data.items():
            if field in setting_mappings:
                save_setting(setting_mappings[field], str(value))
        
        log_admin_action("Updated organization settings")
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Organization settings updated'})
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/organization/logo', methods=['POST'])
@admin_required
@rate_limit(max_requests=5, window=300)
def upload_organization_logo():
    """Upload organization logo"""
    try:
        from werkzeug.utils import secure_filename
        from flask import current_app
        
        if 'logo' not in request.files:
            return jsonify({'success': False, 'error': 'No logo file provided'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
        if not file.filename.lower().endswith(tuple(allowed_extensions)):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Update setting
        save_setting('LOGO_FILENAME', filename)
        log_admin_action(f"Uploaded organization logo: {filename}")
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Logo uploaded successfully',
            'data': {'filename': filename}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# PAYMENT BOT SETTINGS ENDPOINTS
# ============================================================================

@settings_api.route('/payment-bot', methods=['GET'])
@admin_required
def get_payment_bot_settings():
    """Get payment bot settings"""
    try:
        settings = {
            'enable_email_payment_bot': get_setting('ENABLE_EMAIL_PAYMENT_BOT', 'False') == 'True',
            'bank_email_from': get_setting('BANK_EMAIL_FROM'),
            'bank_email_subject': get_setting('BANK_EMAIL_SUBJECT'),
            'bank_email_name_confidence': int(get_setting('BANK_EMAIL_NAME_CONFIDANCE', '85')),
            'gmail_label_folder_processed': get_setting('GMAIL_LABEL_FOLDER_PROCESSED', 'InteractProcessed')
        }
        return jsonify({'success': True, 'data': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/payment-bot', methods=['PUT'])
@admin_required
@rate_limit(max_requests=10, window=60)
def update_payment_bot_settings():
    """Update payment bot settings"""
    try:
        schema = PaymentBotSchema()
        data = schema.load(request.json, partial=True)
        
        # Map fields to setting keys
        setting_mappings = {
            'enable_email_payment_bot': 'ENABLE_EMAIL_PAYMENT_BOT',
            'bank_email_from': 'BANK_EMAIL_FROM',
            'bank_email_subject': 'BANK_EMAIL_SUBJECT',
            'bank_email_name_confidence': 'BANK_EMAIL_NAME_CONFIDANCE',  # Note: typo in original
            'gmail_label_folder_processed': 'GMAIL_LABEL_FOLDER_PROCESSED'
        }
        
        # Update settings
        for field, value in data.items():
            if field in setting_mappings:
                save_setting(setting_mappings[field], str(value))
        
        log_admin_action("Updated payment bot settings")
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payment bot settings updated'})
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ACTIVITY TAGS ENDPOINTS
# ============================================================================

@settings_api.route('/activity-tags', methods=['GET'])
@admin_required
def get_activity_tags():
    """Get activity tags"""
    try:
        activity_list_json = get_setting('ACTIVITY_LIST', '[]')
        activity_list = json.loads(activity_list_json) if activity_list_json else []
        
        return jsonify({'success': True, 'data': {'tags': activity_list}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_api.route('/activity-tags', methods=['PUT'])
@admin_required
@rate_limit(max_requests=10, window=60)
def update_activity_tags():
    """Update activity tags"""
    try:
        tags = request.json.get('tags', [])
        
        # Validate tags
        if not isinstance(tags, list):
            return jsonify({'success': False, 'error': 'Tags must be an array'}), 400
        
        # Clean and filter tags
        clean_tags = [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]
        
        # Save to settings
        save_setting('ACTIVITY_LIST', json.dumps(clean_tags))
        log_admin_action(f"Updated activity tags: {len(clean_tags)} tags")
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Activity tags updated',
            'data': {'tags': clean_tags}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_admin_action(action):
    """Log admin action for audit trail"""
    admin_email = session.get('admin_email', 'unknown')
    log = AdminActionLog(
        admin_email=admin_email,
        action=action,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(log)

def save_setting(key, value):
    """Save or update a setting"""
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    return setting