# Organization-Specific Email Configuration Implementation

## Overview

This implementation provides a complete backend architecture for organization-specific email settings in the Flask Minipass application. Each organization can now have its own email configuration while maintaining backward compatibility with the existing Gmail system.

## Architecture

### 1. Database Models

#### Organization Model (`models.py`)
- **Purpose**: Store organization-specific email configurations
- **Key Fields**:
  - `name`: Organization name (e.g., "LHGI")
  - `domain`: Email domain part (e.g., "lhgi" for lhgi@minipass.me)
  - `mail_server`: SMTP server (e.g., "mail.minipass.me")
  - `mail_port`: SMTP port (default 587)
  - `mail_use_tls/mail_use_ssl`: Security settings
  - `mail_username`: SMTP username
  - `mail_password`: Encrypted password
  - `mail_sender_name`: Display name for emails
  - `email_enabled`: Enable/disable flag
  - `fallback_to_system_email`: Fallback to Gmail if org email fails

#### Updated Models
- **User**: Added `organization_id` foreign key for email context
- **Activity**: Added `organization_id` foreign key for email context

### 2. Email Configuration Management (`utils.py`)

#### Core Functions

1. **`get_email_config_for_context(user, activity, organization_id)`**
   - Determines appropriate email configuration based on priority:
   - Priority: `organization_id` > `activity.organization` > `user.organization` > system default

2. **`create_organization_email_config(...)`**
   - Creates new organization with email settings
   - Encrypts passwords for secure storage
   - Validates unique domain constraints

3. **`update_organization_email_config(org_id, **kwargs)`**
   - Updates existing organization settings
   - Handles password encryption
   - Maintains audit trail

4. **`test_organization_email_config(org_id)`**
   - Tests SMTP connection for organization
   - Returns success/failure with detailed messages

#### Updated Email Functions

1. **`send_email(..., email_config=None)`**
   - Enhanced to accept organization-specific configuration
   - Falls back to system settings if no org config provided
   - Supports both TLS and SSL connections

2. **`send_email_async(app, user=None, activity=None, organization_id=None, ...)`**
   - Automatically determines email configuration based on context
   - Logs which configuration type was used (org vs system)
   - Maintains backward compatibility

### 3. API Endpoints (`app.py`)

#### Organization Management Routes

1. **`GET /admin/organizations`**
   - Lists all organizations with email configurations
   - Returns JSON with organization details

2. **`POST /admin/organizations/create`**
   - Creates new organization with email settings
   - Validates required fields
   - Logs admin actions

3. **`PUT /admin/organizations/<id>/update`**
   - Updates organization email configuration
   - Handles partial updates
   - Maintains audit trail

4. **`POST /admin/organizations/<id>/test`**
   - Tests organization email configuration
   - Returns detailed success/failure information

5. **`POST /admin/organizations/<id>/toggle`**
   - Enables/disables organization email
   - Allows quick activation control

6. **`DELETE /admin/organizations/<id>/delete`**
   - Soft deletes organization (marks inactive)
   - Preserves data for audit purposes

7. **`POST /admin/create-test-org`** (Development)
   - Creates LHGI test organization with provided credentials
   - For development and testing purposes

### 4. Management Interface (`templates/partials/settings_org.html`)

#### Features
- **Organization List**: Displays all configured organizations
- **Create/Edit Modal**: Full-featured form for organization management
- **Action Buttons**: Test, Edit, Enable/Disable, Delete
- **Real-time Status**: Shows enabled/disabled status and configuration details
- **Test Functionality**: One-click email configuration testing

#### JavaScript Functions
- `loadOrganizations()`: Fetches and displays organization list
- `saveOrganization()`: Creates or updates organizations
- `testOrganizationEmail()`: Tests email configuration
- `toggleOrganizationEmail()`: Enables/disables email
- `createTestOrg()`: Creates test LHGI organization

### 5. Database Migration

#### Migration File: `add_organization_email_support.py`
- Creates `organizations` table with all necessary fields
- Adds `organization_id` foreign keys to `user` and `activity` tables
- Includes proper indexes and constraints
- Supports rollback functionality

## Test Credentials Setup

### LHGI Organization
- **Email**: lhgi@minipass.me
- **Mail Server**: mail.minipass.me
- **Password**: monsterinc00
- **Sender Name**: LHGI

## Usage Examples

### 1. Create Organization via API

```python
import requests

data = {
    "name": "LHGI",
    "domain": "lhgi",
    "mail_server": "mail.minipass.me",
    "mail_username": "lhgi@minipass.me",
    "mail_password": "monsterinc00",
    "mail_sender_name": "LHGI",
    "mail_port": 587,
    "mail_use_tls": True
}

response = requests.post("http://127.0.0.1:8890/admin/organizations/create", 
                        json=data, cookies={"session": "..."})
```

### 2. Send Email with Organization Context

```python
from utils import send_email_async
from models import User, Activity

user = User.query.filter_by(email="test@example.com").first()
activity = Activity.query.filter_by(organization_id=1).first()

send_email_async(
    app=app,
    user=user,
    activity=activity,
    subject="Test Email",
    to_email="test@example.com",
    template_name="test.html",
    context={"message": "Hello from LHGI!"}
)
```

### 3. Manual Email Configuration

```python
from utils import get_email_config_for_context, send_email

# Get organization-specific config
config = get_email_config_for_context(user=user, activity=activity)

# Send email with specific config
send_email(
    subject="Test Email",
    to_email="test@example.com", 
    template_name="test.html",
    context={"message": "Hello!"},
    email_config=config
)
```

## Security Features

### 1. Password Encryption
- Passwords are encrypted using base64 encoding (development)
- Production should use proper encryption (Fernet/AES)
- Passwords never stored in plain text

### 2. Access Control
- All management endpoints require admin authentication
- Session-based access control
- Admin action logging for audit trail

### 3. Validation
- Input validation for all email settings
- Domain uniqueness constraints
- Required field validation
- SMTP connection testing

## Backward Compatibility

### 1. Existing Email System
- System continues to work with global Gmail settings
- No breaking changes to existing email functions
- Graceful fallback when no organization config exists

### 2. Migration Path
- Organizations can be added gradually
- Users/activities without org assignment use system default
- Smooth transition from single to multi-tenant email

### 3. Configuration Priority
1. Direct organization_id parameter
2. Activity's organization
3. User's organization  
4. System default (Gmail)

## Error Handling

### 1. Email Sending
- Automatic fallback to system email if organization email fails
- Detailed error logging with configuration type used
- Graceful degradation for missing configurations

### 2. Configuration Testing
- Comprehensive SMTP connection testing
- Detailed error messages for troubleshooting
- Connection timeout handling

### 3. API Error Responses
- Structured JSON error responses
- HTTP status codes for different error types
- User-friendly error messages

## Monitoring and Logging

### 1. Admin Action Log
- All organization management actions logged
- Email test results logged
- Configuration changes tracked

### 2. Email Logs
- Enhanced with configuration type (org vs system)
- Mail server information included
- Success/failure tracking

### 3. Performance Monitoring
- Email sending performance by organization
- Configuration test results
- Failure rate tracking

## Future Enhancements

### 1. Advanced Features
- Email template customization per organization
- Organization-specific email signatures
- Advanced routing rules
- Bulk email management

### 2. Security Improvements
- Proper encryption for sensitive data
- Certificate-based authentication
- OAuth2 integration
- Password rotation policies

### 3. Monitoring Enhancements
- Email delivery analytics
- Performance dashboards
- Alert systems for failures
- Cost tracking per organization

## Testing

### Test Script: `test_organization_email.py`
- Comprehensive testing of all functionality
- Login and session management
- Organization CRUD operations
- Email configuration testing
- UI validation

### Manual Testing Steps
1. Access http://127.0.0.1:8890/setup
2. Navigate to "Organization" tab
3. Create LHGI test organization
4. Test email configuration
5. Create activity with organization
6. Send test email and verify organization-specific settings

## Deployment Notes

### 1. Database Migration
```bash
# Run migration to create Organization table
flask db upgrade
```

### 2. Environment Variables
```bash
# Optional: Set encryption key for production
export MINIPASS_ENCRYPTION_KEY="your-encryption-key-here"
```

### 3. Server Configuration
- Ensure mail.minipass.me is accessible
- Configure firewall for SMTP ports
- Set up DNS records for @minipass.me domain

This implementation provides a robust, scalable foundation for organization-specific email configuration while maintaining full backward compatibility with the existing system.