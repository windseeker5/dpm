"""
Chatbot Configuration Settings
"""
import os

# AI Provider Settings
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
GOOGLE_AI_API_KEY = os.environ.get('GOOGLE_AI_API_KEY')  # Gemini API key
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')  # Groq API key

# Cost Management
CHATBOT_DAILY_BUDGET_CENTS = int(os.environ.get('CHATBOT_DAILY_BUDGET_CENTS', 1000))  # $10
CHATBOT_MONTHLY_BUDGET_CENTS = int(os.environ.get('CHATBOT_MONTHLY_BUDGET_CENTS', 10000))  # $100

# Feature Flags
CHATBOT_ENABLE_ANTHROPIC = os.environ.get('CHATBOT_ENABLE_ANTHROPIC', 'false').lower() == 'true'
CHATBOT_ENABLE_OPENAI = os.environ.get('CHATBOT_ENABLE_OPENAI', 'false').lower() == 'true'
CHATBOT_ENABLE_OLLAMA = os.environ.get('CHATBOT_ENABLE_OLLAMA', 'false').lower() == 'true'  # Disabled by default
CHATBOT_ENABLE_GEMINI = os.environ.get('CHATBOT_ENABLE_GEMINI', 'true').lower() == 'true'  # Enabled by default
CHATBOT_ENABLE_GROQ = os.environ.get('CHATBOT_ENABLE_GROQ', 'true').lower() == 'true'  # Enabled by default (fallback)

# Query Settings
MAX_QUERY_TIMEOUT_SECONDS = 30
MAX_RESULT_ROWS = 1000
DEFAULT_AI_MODEL = 'gemini-2.5-flash'  # Gemini 2.5 Flash (WORKS! Free tier available)

# Model preferences (in order of preference)
# Note: Groq is used as automatic fallback when Gemini hits rate limits
# Updated Jan 2026: Gemini 1.5/2.0 models retired Sept 2025, use 2.5 series
PREFERRED_MODELS = [
    'gemini-2.5-flash',           # Primary Gemini - free tier
    'llama-3.3-70b-versatile',    # Groq fallback: 14,400 RPD, 30 RPM
    'gemini-2.5-flash-lite',      # Gemini backup - lighter/faster
    'llama-3.1-8b-instant',       # Groq fast model
    'gemini-2.5-pro',             # Gemini quality (limited free tier)
]

# Security Settings
ALLOWED_SQL_KEYWORDS = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT']
BLOCKED_SQL_KEYWORDS = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']

# UI Settings
CHAT_MESSAGE_MAX_LENGTH = 2000
CONVERSATION_TIMEOUT_HOURS = 24