"""
Chatbot Configuration Settings
"""
import os

# AI Provider Settings
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

# Cost Management
CHATBOT_DAILY_BUDGET_CENTS = int(os.environ.get('CHATBOT_DAILY_BUDGET_CENTS', 1000))  # $10
CHATBOT_MONTHLY_BUDGET_CENTS = int(os.environ.get('CHATBOT_MONTHLY_BUDGET_CENTS', 10000))  # $100

# Feature Flags
CHATBOT_ENABLE_ANTHROPIC = os.environ.get('CHATBOT_ENABLE_ANTHROPIC', 'false').lower() == 'true'
CHATBOT_ENABLE_OPENAI = os.environ.get('CHATBOT_ENABLE_OPENAI', 'false').lower() == 'true'
CHATBOT_ENABLE_OLLAMA = os.environ.get('CHATBOT_ENABLE_OLLAMA', 'true').lower() == 'true'

# Query Settings
MAX_QUERY_TIMEOUT_SECONDS = 30
MAX_RESULT_ROWS = 1000
DEFAULT_AI_MODEL = 'dolphin-mistral:latest'

# Security Settings
ALLOWED_SQL_KEYWORDS = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT']
BLOCKED_SQL_KEYWORDS = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']

# UI Settings
CHAT_MESSAGE_MAX_LENGTH = 2000
CONVERSATION_TIMEOUT_HOURS = 24