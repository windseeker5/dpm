#!/usr/bin/env python3
"""
Wrapper script to run debug_email_recovery.py with Flask app context
"""

import sys
from app import app

# Remove the wrapper script name from args
sys.argv.pop(0)

# Import and run the debug script within Flask app context
with app.app_context():
    import debug_email_recovery
    debug_email_recovery.main()
