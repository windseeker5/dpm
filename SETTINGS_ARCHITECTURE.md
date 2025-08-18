# Settings Management Architecture - Backend Improvements

## Overview

This document outlines the comprehensive backend architecture improvements for the Minipass settings/setup functionality. The new architecture transforms the monolithic settings management into a scalable, secure, and maintainable system.

## Architecture Improvements Summary

### 1. RESTful API Design

**Before:**
- Single POST route handling all settings
- Monolithic form submission
- No API endpoints for individual sections
- Full page reloads for all updates

**After:**
- RESTful API with logical endpoints
- Individual sections manageable independently
- Proper HTTP methods (GET, POST, PUT, DELETE)
- JSON responses for frontend integration

#### API Structure:
```
/api/v1/settings/
├── admin/               # Admin account management
├── email/              # Email configuration & templates
├── organization/       # Organization settings & logo
├── application/        # App-level settings
├── payment-bot/        # Email payment bot configuration
└── activity-tags/      # Activity management
```

### 2. Enhanced Data Storage Architecture

**Before:**
- Simple key-value pairs in Settings table
- No validation or type checking
- No audit trail
- Mixed storage patterns

**After:**
- Structured settings with schemas
- Type validation and constraints
- Encrypted storage for sensitive data
- Complete audit trail
- Proper normalization

#### New Database Schema:

```sql
-- Setting definitions and validation rules
setting_schemas (
    id, key, name, description, type, scope,
    default_value, validation_rules, is_sensitive,
    is_required, is_public, created_at, updated_at
)

-- Actual setting values with encryption support
setting_values (
    id, key, value, encrypted_value,
    created_at, updated_at, created_by, updated_by
)

-- Complete audit trail
setting_change_logs (
    id, setting_key, old_value, new_value,
    changed_by, changed_at, change_reason,
    ip_address, user_agent
)
```

### 3. Security Enhancements

#### Authentication & Authorization:
- Admin-only access with session validation
- Rate limiting on all endpoints
- IP whitelisting capability
- Elevated privileges for sensitive operations

#### Data Protection:
- Encryption for sensitive settings (passwords, API keys)
- Input validation and sanitization
- CSRF protection
- SQL injection prevention

#### Audit & Monitoring:
- Complete action logging
- Failed login attempt tracking
- Sensitive setting access logging
- Security event monitoring

### 4. Backup & Restore System

**Before:**
- Basic backup integrated into settings page
- No restore functionality
- No validation or metadata

**After:**
- Dedicated backup/restore API
- Multiple backup types (full, settings, data)
- Backup validation and metadata
- Automatic restore points
- Rollback capabilities

#### Features:
- **Backup Types**: Full, settings-only, data-only
- **Validation**: Database integrity checks
- **Metadata**: Creation info, contents, version
- **Restore Points**: Automatic before major operations
- **Security**: Download restrictions, file validation

### 5. Email Template Management

**Before:**
- Email templates mixed with SMTP settings
- No structured template management
- Limited customization options

**After:**
- Dedicated email template API
- Event-based template organization
- Template validation and testing
- Theme support and customization

#### Template Events:
- `pass_created` - New pass notifications
- `pass_redeemed` - Pass redemption confirmations
- `payment_received` - Payment confirmations
- `payment_late` - Late payment reminders
- `signup` - Registration confirmations
- `survey_invitation` - Survey invitations

### 6. Settings Validation System

#### Type System:
- **STRING**: Basic text values
- **INTEGER**: Numeric integers with range validation
- **FLOAT**: Decimal numbers with precision
- **BOOLEAN**: True/false values
- **EMAIL**: Email format validation
- **URL**: URL format validation
- **PASSWORD**: Sensitive encrypted storage
- **JSON**: Structured data validation
- **TEXT**: Large text content

#### Validation Rules:
```json
{
  "min_length": 8,
  "max_length": 255,
  "min_value": 0,
  "max_value": 100,
  "pattern": "^[a-zA-Z0-9]+$",
  "allowed_values": ["option1", "option2"]
}
```

## Implementation Files

### Core API Files:
- `/api/settings.py` - Main settings API endpoints
- `/api/backup.py` - Backup and restore system
- `/decorators.py` - Security and validation decorators
- `/models/settings.py` - Enhanced settings models
- `/config/security.py` - Security configuration

### Database Migration:
- `/migrations/migrate_to_enhanced_settings.py` - Migration script

### Testing:
- `/tests/test_settings_api.py` - Comprehensive test suite

## Key Classes and Components

### SettingsManager
Central settings management with validation and caching:
```python
# Get setting with type conversion and default
value = SettingsManager.get('MAIL_PORT', 587)

# Set with validation and audit trail
SettingsManager.set('ORG_NAME', 'My Company', 
                   changed_by='admin@example.com',
                   change_reason='Organization rebranding')

# Get settings by scope
email_settings = SettingsManager.get_by_scope(SettingScope.EMAIL)
```

### SecurityConfig
Centralized security configuration:
```python
# Password validation
errors = SecurityConfig.validate_password('weak')

# Rate limiting configuration
RATE_LIMITS = {
    'admin_create': {'requests': 5, 'window': 300},
    'settings_update': {'requests': 20, 'window': 60}
}
```

### AuditLogger
Comprehensive audit logging:
```python
# Log admin actions
AuditLogger.log_admin_action('SETTING_CHANGED', 
                           admin_email, 
                           'Updated SMTP settings')

# Log security events
AuditLogger.log_failed_login(email, ip_address, user_agent)
```

## Security Best Practices Implemented

### 1. Input Validation
- Schema-based validation for all settings
- Type checking and format validation
- Range and pattern validation
- SQL injection prevention

### 2. Authentication & Authorization
- Session-based authentication
- Admin-only access controls
- Rate limiting on sensitive operations
- IP whitelisting capability

### 3. Data Protection
- Encryption for sensitive settings
- Secure password requirements
- CSRF protection
- XSS prevention headers

### 4. Audit & Monitoring
- Complete change audit trail
- Failed authentication logging
- Sensitive data access tracking
- Security event monitoring

### 5. File Security
- Secure filename validation
- File type restrictions
- Upload size limits
- Path traversal prevention

## Migration Strategy

### Phase 1: Preparation
1. Deploy new models and API alongside existing system
2. Run migration script to populate new tables
3. Validate data integrity and settings functionality

### Phase 2: API Integration
1. Update frontend to use new API endpoints
2. Implement progressive enhancement
3. Test all settings functionality

### Phase 3: Cutover
1. Switch to new settings system
2. Deprecate old monolithic route
3. Monitor for issues and performance

### Phase 4: Cleanup
1. Remove legacy settings code
2. Update documentation
3. Train administrators on new features

## Performance Considerations

### Caching Strategy
- In-memory caching for frequently accessed settings
- 5-minute cache TTL with manual invalidation
- Scope-based cache warming
- Public settings cache for frontend

### Database Optimization
- Indexed setting keys for fast lookups
- Efficient audit log queries
- Proper relationship mapping
- Connection pooling support

### API Performance
- Rate limiting to prevent abuse
- Efficient JSON serialization
- Minimal database queries per request
- Proper HTTP status codes

## Monitoring and Alerting

### Key Metrics
- Settings API response times
- Failed authentication attempts
- Rate limit violations
- Backup success/failure rates
- Setting validation errors

### Alert Conditions
- Multiple failed login attempts
- Suspicious IP access patterns
- Backup failures
- Setting validation errors
- Encryption key issues

## Testing Strategy

### Unit Tests
- Settings validation logic
- Encryption/decryption functions
- API endpoint functionality
- Rate limiting mechanisms

### Integration Tests
- End-to-end settings workflows
- Backup and restore operations
- Email template management
- Admin account management

### Security Tests
- Authentication bypass attempts
- Input validation edge cases
- Rate limiting effectiveness
- Encryption key handling

## Future Enhancements

### Short Term
- Web UI for the new API endpoints
- Real-time settings synchronization
- Advanced backup scheduling
- Setting import/export tools

### Medium Term
- Role-based access control
- Setting approval workflows
- Integration with external config systems
- Multi-tenant settings support

### Long Term
- Settings version control
- Automated rollback triggers
- Machine learning for anomaly detection
- GraphQL API support

## Conclusion

This enhanced settings architecture provides:

1. **Scalability**: RESTful API design supports future growth
2. **Security**: Comprehensive protection for sensitive data
3. **Maintainability**: Clean separation of concerns and proper validation
4. **Auditability**: Complete trail of all configuration changes
5. **Flexibility**: Type system and validation rules support diverse settings
6. **Reliability**: Backup/restore system ensures data safety

The modular design allows for incremental adoption while maintaining backward compatibility with existing functionality.