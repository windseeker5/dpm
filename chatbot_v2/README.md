# AI Analytics Chatbot - Gemini Setup Guide

## Quick Start

The AI Analytics chatbot now uses **Google Gemini** (free tier) for natural language to SQL query generation.

## Getting Your Gemini API Key

### Step 1: Visit Google AI Studio
Go to: https://ai.google.dev/aistudio

### Step 2: Sign In
- Use your personal Gmail account
- No credit card required

### Step 3: Get API Key
1. Click "Get API Key" button
2. Create a new API key or use an existing one
3. Copy the API key

### Step 4: Add to Environment
Add this line to your `.env` file:
```bash
GOOGLE_AI_API_KEY=your_api_key_here
```

## Free Tier Limits

Google Gemini offers generous free tier limits:

- **Gemini 1.5 Flash**: 15 requests/min, 1M tokens/min, 1,500 requests/day
- **Gemini 1.5 Flash-8B**: Same limits, even faster
- **Gemini 1.5 Pro**: 2 requests/min, 32K tokens/min, 50 requests/day

**For 2 prototype users:** You have 30-75x headroom over expected usage!

## Configuration Options

All configuration is in `chatbot_v2/config.py`:

```python
# Enable/disable Gemini
CHATBOT_ENABLE_GEMINI = True  # Default: enabled

# Default model (fastest free tier model)
DEFAULT_AI_MODEL = 'gemini-1.5-flash'

# Budget tracking (optional, free tier = $0)
CHATBOT_DAILY_BUDGET_CENTS = 1000    # $10
CHATBOT_MONTHLY_BUDGET_CENTS = 10000 # $100
```

## Testing the Integration

### 1. Check Provider Status
Visit: http://localhost:5000/chatbot/status

You should see:
```json
{
  "gemini_direct": {
    "api_configured": true,
    "available": true,
    "models": ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"],
    "model_count": 3
  }
}
```

### 2. Access the Chatbot
Visit: http://localhost:5000/chatbot

### 3. Try a Sample Query
- "Show me all users"
- "What is our total revenue this month?"
- "How many unpaid passports do we have?"

## Error Handling

If Gemini is unavailable, users will see:
> ⚠️ AI Analytics temporarily unavailable. Please contact Minipass support.

This ensures a clean user experience without technical error messages.

## Architecture

### Provider Structure
```
chatbot_v2/
├── providers/
│   ├── gemini.py          # Google Gemini provider
│   ├── ollama.py          # (legacy, disabled)
│   └── __init__.py        # Provider exports
├── ai_providers.py        # Provider manager
├── query_engine.py        # SQL generation engine
├── routes.py              # Flask endpoints
└── config.py              # Configuration
```

### Request Flow
1. User asks question in natural language
2. `routes.py` validates and forwards to `query_engine.py`
3. `query_engine.py` sends prompt to Gemini provider
4. Gemini generates SQL query
5. SQL executes against database
6. Results formatted and returned to user

## Monitoring

Query logs are stored in the `QueryLog` database table:
- Question asked
- SQL generated
- Execution time
- Token usage
- Cost (always $0 on free tier)
- Success/error status

## Upgrading to Paid Tier

If you exceed free tier limits:
1. Enable billing in Google Cloud Console
2. Link AI Studio to Cloud project
3. Costs are very low: ~$0.001 per query

## Troubleshooting

### "GOOGLE_AI_API_KEY not configured"
- Add the API key to your `.env` file
- Restart Flask server

### "Gemini API not reachable"
- Check internet connection
- Verify API key is valid
- Check https://status.cloud.google.com/

### "AI Analytics temporarily unavailable"
- Check `/chatbot/status` endpoint
- Review Flask logs for detailed error
- Verify API key hasn't expired

## Support

For questions or issues:
- Email: support@minipass.com
- Documentation: https://docs.minipass.com
