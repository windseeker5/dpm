"""
AI Analytics Chatbot Module v2
Professional implementation with multi-provider AI support
"""

__version__ = "2.0.0"
__author__ = "Minipass Team"

# Only import Flask routes when Flask is available
try:
    from .routes import chatbot_bp
    __all__ = ['chatbot_bp']
except ImportError:
    # Flask not available, skip route imports
    __all__ = []