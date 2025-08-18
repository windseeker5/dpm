# tests/test_settings_api.py - Comprehensive tests for settings API
import pytest
import json
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app import app
from models import db, Admin, Setting
from models.settings import SettingSchema, SettingValue, SettingChangeLog, SettingsManager, SettingType, SettingScope
import bcrypt

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test admin
            admin = Admin(
                email='test@example.com',
                password_hash=bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()
            )
            db.session.add(admin)
            db.session.commit()
            
            # Create test setting schema
            schema = SettingSchema(
                key='TEST_SETTING',
                name='Test Setting',
                description='A test setting',
                type=SettingType.STRING,
                scope=SettingScope.SYSTEM,
                default_value='default_value'
            )
            db.session.add(schema)
            db.session.commit()
            
        yield client

@pytest.fixture
def auth_headers():
    """Headers for authenticated requests"""
    return {'X-Admin-Email': 'test@example.com'}

# ============================================================================
# ADMIN MANAGEMENT TESTS
# ============================================================================

def test_get_admins(client, auth_headers):
    """Test getting list of admins"""
    with client.session_transaction() as sess:
        sess['admin'] = True
        sess['admin_email'] = 'test@example.com'
    
    response = client.get('/api/v1/settings/admin', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['data']) == 1
    assert data['data'][0]['email'] == 'test@example.com'

def test_create_admin(client, auth_headers):
    """Test creating new admin"""
    with client.session_transaction() as sess:
        sess['admin'] = True
        sess['admin_email'] = 'test@example.com'
    
    admin_data = {
        'email': 'new@example.com',
        'password': 'newpassword123'
    }
    
    response = client.post('/api/v1/settings/admin',
                          json=admin_data,
                          headers=auth_headers)
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['email'] == 'new@example.com'

def test_create_admin_duplicate_email(client, auth_headers):
    """Test creating admin with duplicate email"""
    with client.session_transaction() as sess:
        sess['admin'] = True
        sess['admin_email'] = 'test@example.com'
    
    admin_data = {
        'email': 'test@example.com',  # Duplicate
        'password': 'password123'
    }
    
    response = client.post('/api/v1/settings/admin',
                          json=admin_data,
                          headers=auth_headers)
    assert response.status_code == 409
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'already exists' in data['error']

def test_update_admin(client, auth_headers):
    """Test updating admin"""
    with client.session_transaction() as sess:
        sess['admin'] = True
        sess['admin_email'] = 'test@example.com'
    
    admin = Admin.query.filter_by(email='test@example.com').first()
    
    update_data = {
        'email': 'updated@example.com'
    }
    
    response = client.put(f'/api/v1/settings/admin/{admin.id}',
                         json=update_data,
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['email'] == 'updated@example.com'

def test_delete_admin(client, auth_headers):
    """Test deleting admin"""
    with client.session_transaction() as sess:
        sess['admin'] = True
        sess['admin_email'] = 'test@example.com'
    
    # Create second admin first
    admin2 = Admin(
        email='delete@example.com',
        password_hash=bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode()
    )
    db.session.add(admin2)
    db.session.commit()
    
    response = client.delete(f'/api/v1/settings/admin/{admin2.id}',
                           headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True

def test_delete_last_admin(client, auth_headers):
    """Test preventing deletion of last admin"""
    with client.session_transaction() as sess:
        sess['admin'] = True
        sess['admin_email'] = 'test@example.com'
    
    admin = Admin.query.filter_by(email='test@example.com').first()
    
    response = client.delete(f'/api/v1/settings/admin/{admin.id}',
                           headers=auth_headers)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'last admin' in data['error']

# ============================================================================
# EMAIL CONFIGURATION TESTS
# ============================================================================

def test_get_email_config(client, auth_headers):
    """Test getting email configuration"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    # Set up test email settings
    SettingsManager.set('MAIL_SERVER', 'smtp.example.com', 'test')
    SettingsManager.set('MAIL_PORT', '587', 'test')
    
    response = client.get('/api/v1/settings/email/config', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['data']['mail_server'] == 'smtp.example.com'
    assert data['data']['mail_port'] == 587

def test_update_email_config(client, auth_headers):
    """Test updating email configuration"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    email_config = {
        'mail_server': 'new.smtp.example.com',
        'mail_port': 465,
        'mail_use_tls': True
    }
    
    response = client.put('/api/v1/settings/email/config',
                         json=email_config,
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify settings were saved
    assert SettingsManager.get('MAIL_SERVER') == 'new.smtp.example.com'
    assert SettingsManager.get('MAIL_PORT') == '465'

@patch('utils.send_email_async')
def test_test_email_config(mock_send_email, client, auth_headers):
    """Test email configuration testing"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    test_data = {'test_email': 'test@example.com'}
    
    response = client.post('/api/v1/settings/email/test',
                          json=test_data,
                          headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    mock_send_email.assert_called_once()

# ============================================================================
# EMAIL TEMPLATES TESTS
# ============================================================================

def test_get_email_templates(client, auth_headers):
    """Test getting email templates"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    response = client.get('/api/v1/settings/email/templates', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'pass_created' in data['data']
    assert 'signup' in data['data']

def test_update_email_template(client, auth_headers):
    """Test updating email template"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    template_data = {
        'subject': 'Welcome to our service!',
        'title': 'Welcome',
        'theme': 'success'
    }
    
    response = client.put('/api/v1/settings/email/templates/signup',
                         json=template_data,
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True

def test_update_invalid_email_template(client, auth_headers):
    """Test updating invalid email template"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    template_data = {'subject': 'Test'}
    
    response = client.put('/api/v1/settings/email/templates/invalid_event',
                         json=template_data,
                         headers=auth_headers)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] is False

# ============================================================================
# ORGANIZATION SETTINGS TESTS
# ============================================================================

def test_get_organization_settings(client, auth_headers):
    """Test getting organization settings"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    response = client.get('/api/v1/settings/organization', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'org_name' in data['data']
    assert 'default_pass_amount' in data['data']

def test_update_organization_settings(client, auth_headers):
    """Test updating organization settings"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    org_data = {
        'org_name': 'My Updated Organization',
        'default_pass_amount': 75.0
    }
    
    response = client.put('/api/v1/settings/organization',
                         json=org_data,
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True

@patch('werkzeug.utils.secure_filename')
@patch('os.makedirs')
def test_upload_organization_logo(mock_makedirs, mock_secure_filename, client, auth_headers):
    """Test uploading organization logo"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    mock_secure_filename.return_value = 'logo.png'
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        temp_file.write(b'fake image data')
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, 'rb') as test_file:
            response = client.post('/api/v1/settings/organization/logo',
                                 data={'logo': (test_file, 'logo.png')},
                                 headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['filename'] == 'logo.png'
    finally:
        os.unlink(temp_file_path)

# ============================================================================
# ACTIVITY TAGS TESTS
# ============================================================================

def test_get_activity_tags(client, auth_headers):
    """Test getting activity tags"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    SettingsManager.set('ACTIVITY_LIST', '["hockey", "yoga", "swimming"]', 'test')
    
    response = client.get('/api/v1/settings/activity-tags', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'hockey' in data['data']['tags']
    assert 'yoga' in data['data']['tags']

def test_update_activity_tags(client, auth_headers):
    """Test updating activity tags"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    tags_data = {'tags': ['football', 'basketball', 'tennis']}
    
    response = client.put('/api/v1/settings/activity-tags',
                         json=tags_data,
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['data']['tags']) == 3

# ============================================================================
# SETTINGS MANAGER TESTS
# ============================================================================

def test_settings_manager_get_set():
    """Test SettingsManager get/set functionality"""
    # Test setting and getting a value
    SettingsManager.set('TEST_SETTING', 'test_value', 'test_user')
    value = SettingsManager.get('TEST_SETTING')
    assert value == 'test_value'
    
    # Test getting default value
    value = SettingsManager.get('NONEXISTENT_SETTING', 'default')
    assert value == 'default'

def test_settings_manager_validation():
    """Test SettingsManager validation"""
    # Create a schema with validation rules
    schema = SettingSchema(
        key='VALIDATED_SETTING',
        name='Validated Setting',
        type=SettingType.INTEGER,
        scope=SettingScope.SYSTEM,
        validation_rules={'min_value': 10, 'max_value': 100}
    )
    db.session.add(schema)
    db.session.commit()
    
    # Test valid value
    SettingsManager.set('VALIDATED_SETTING', '50', 'test_user')
    assert SettingsManager.get('VALIDATED_SETTING') == '50'
    
    # Test invalid value
    with pytest.raises(ValueError):
        SettingsManager.set('VALIDATED_SETTING', '5', 'test_user')  # Below minimum

def test_settings_manager_encryption():
    """Test encryption for sensitive settings"""
    # Create a sensitive setting schema
    schema = SettingSchema(
        key='SENSITIVE_SETTING',
        name='Sensitive Setting',
        type=SettingType.PASSWORD,
        scope=SettingScope.SECURITY,
        is_sensitive=True
    )
    db.session.add(schema)
    db.session.commit()
    
    # Set sensitive value
    SettingsManager.set('SENSITIVE_SETTING', 'secret_password', 'test_user')
    
    # Value should be retrievable
    value = SettingsManager.get('SENSITIVE_SETTING')
    assert value == 'secret_password'
    
    # But stored value should be encrypted
    setting_value = SettingValue.query.filter_by(key='SENSITIVE_SETTING').first()
    assert setting_value.value is None
    assert setting_value.encrypted_value is not None
    assert setting_value.encrypted_value != 'secret_password'

def test_settings_manager_audit_trail():
    """Test audit trail functionality"""
    initial_count = SettingChangeLog.query.count()
    
    # Make a change
    SettingsManager.set('TEST_SETTING', 'new_value', 'test_user', 'Testing audit trail')
    
    # Check audit log was created
    assert SettingChangeLog.query.count() == initial_count + 1
    
    log = SettingChangeLog.query.filter_by(setting_key='TEST_SETTING').first()
    assert log.changed_by == 'test_user'
    assert log.change_reason == 'Testing audit trail'
    assert log.new_value == 'new_value'

def test_settings_manager_scope_filtering():
    """Test getting settings by scope"""
    # Create settings in different scopes
    email_schema = SettingSchema(
        key='EMAIL_TEST',
        name='Email Test',
        type=SettingType.STRING,
        scope=SettingScope.EMAIL
    )
    org_schema = SettingSchema(
        key='ORG_TEST',
        name='Org Test',
        type=SettingType.STRING,
        scope=SettingScope.ORGANIZATION
    )
    db.session.add_all([email_schema, org_schema])
    db.session.commit()
    
    SettingsManager.set('EMAIL_TEST', 'email_value', 'test')
    SettingsManager.set('ORG_TEST', 'org_value', 'test')
    
    # Get settings by scope
    email_settings = SettingsManager.get_by_scope(SettingScope.EMAIL)
    assert 'EMAIL_TEST' in email_settings
    assert 'ORG_TEST' not in email_settings
    
    org_settings = SettingsManager.get_by_scope(SettingScope.ORGANIZATION)
    assert 'ORG_TEST' in org_settings
    assert 'EMAIL_TEST' not in org_settings

def test_settings_manager_public_settings():
    """Test public settings functionality"""
    # Create public setting
    public_schema = SettingSchema(
        key='PUBLIC_SETTING',
        name='Public Setting',
        type=SettingType.STRING,
        scope=SettingScope.ORGANIZATION,
        is_public=True
    )
    db.session.add(public_schema)
    db.session.commit()
    
    SettingsManager.set('PUBLIC_SETTING', 'public_value', 'test')
    
    public_settings = SettingsManager.get_public_settings()
    assert 'PUBLIC_SETTING' in public_settings
    assert public_settings['PUBLIC_SETTING'] == 'public_value'

# ============================================================================
# AUTHENTICATION AND AUTHORIZATION TESTS
# ============================================================================

def test_unauthorized_access(client):
    """Test that unauthorized requests are rejected"""
    response = client.get('/api/v1/settings/admin')
    assert response.status_code == 401
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert data['code'] == 'AUTH_REQUIRED'

def test_rate_limiting(client, auth_headers):
    """Test rate limiting functionality"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    # Make multiple requests rapidly (assuming rate limit is low for testing)
    with patch('decorators.rate_limit_store', {}):  # Reset rate limit store
        responses = []
        for i in range(15):  # Exceed typical rate limit
            response = client.post('/api/v1/settings/admin',
                                 json={'email': f'test{i}@example.com', 'password': 'pass123'},
                                 headers=auth_headers)
            responses.append(response.status_code)
        
        # At least one request should be rate limited
        assert 429 in responses

def test_input_validation(client, auth_headers):
    """Test input validation"""
    with client.session_transaction() as sess:
        sess['admin'] = True
    
    # Test invalid email format
    invalid_admin = {'email': 'not-an-email', 'password': 'password123'}
    response = client.post('/api/v1/settings/admin',
                          json=invalid_admin,
                          headers=auth_headers)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'errors' in data

if __name__ == '__main__':
    pytest.main([__file__])