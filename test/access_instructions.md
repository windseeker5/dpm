# Unified Settings Access Instructions

## How to Access the Unified Settings Page

1. **Login to the application**
   - Navigate to: http://127.0.0.1:8890/login
   - Use credentials: kdresdell@gmail.com / admin123

2. **Access Unified Settings**
   - Direct URL: http://127.0.0.1:8890/admin/unified-settings
   - Alternative URL: http://127.0.0.1:8890/admin/settings

## What You'll Find

The unified settings page consolidates three main settings sections:

### 📋 Organization Settings
- Organization Name
- Call-back Days configuration
- Logo upload functionality

### 📧 Email Settings  
- Mail server configuration
- SMTP settings (server, port, TLS)
- Mail credentials and sender information

### 🤖 Payment Bot Settings
- Enable/disable email payment bot
- Bank email processing configuration
- Name confidence threshold settings

## Features

- ✅ Single form for all settings
- ✅ Real-time data loading from database
- ✅ Secure form processing with CSRF protection
- ✅ File upload support for organization logos
- ✅ Admin action logging
- ✅ Success/error flash messages
- ✅ Automatic redirect after save

## Technical Details

- **Route**: `/admin/unified-settings` (GET/POST)
- **Alternative Route**: `/admin/settings` (for template compatibility)
- **Template**: `templates/unified_settings.html`
- **Location in Code**: Around line 2225 in `app.py`