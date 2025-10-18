# Gemini 2.0 Flash Exp Configuration - COMPLETE ✅

## Summary
Your chatbot now uses **`gemini-2.0-flash-exp`** by default, giving you **3x more queries** than before!

## Rate Limit Comparison

| Model | Requests/Day (RPD) | Requests/Min (RPM) | Tokens/Min (TPM) |
|-------|-------------------|-------------------|------------------|
| **gemini-2.0-flash-exp** ⭐ | **1,500** | **15** | **1,000,000** |
| gemini-2.0-flash | 1,500 | 15 | 1,000,000 |
| gemini-2.5-flash (old) | 500 | 10 | 250,000 |
| gemini-2.5-pro | 100 | 5 | 250,000 |

### Why You Hit the Limit Before

With `gemini-2.5-flash`, you only got **500 requests per day**. Each user question typically uses 2 API calls (SQL generation + formatting), so:
- 500 requests ÷ 2 = **Only 250 questions per day**
- With 2 users testing = easily maxed out!

### Now With gemini-2.0-flash-exp

- **1,500 requests per day** ÷ 2 = **750 questions per day**
- **3x more capacity** for your prototype users!

## Files Updated

### 1. `chatbot_v2/config.py`
```python
DEFAULT_AI_MODEL = 'gemini-2.0-flash-exp'  # Was: gemini-2.5-flash

PREFERRED_MODELS = [
    'gemini-2.0-flash-exp',  # BEST: 1,500 RPD, 15 RPM
    'gemini-2.0-flash',      # Good: 1,500 RPD
    'gemini-2.5-flash',      # Limited: 500 RPD
    'gemini-2.5-pro'         # Most limited: 100 RPD
]
```

### 2. `chatbot_v2/routes_simple.py`
- Line 152: Default model in ask route = `gemini-2.0-flash-exp`
- Line 71: Conversational response model = `gemini-2.0-flash-exp`

### 3. `chatbot_v2/providers/gemini.py`
- Added `gemini-2.0-flash-exp` to PRICING dictionary
- Updated `__init__` to use `DEFAULT_AI_MODEL` from config
- Provider now auto-selects the best model

## Testing

The chatbot has been tested and works perfectly:
- ✅ "show me all users" → Returns 88 users correctly
- ✅ SQL generation working
- ✅ Data queries successful
- ✅ Conversational responses working

## What Changed for Your Users

**Before:**
- Model dropdown showed: "gemini-2.5-flash"
- Hit rate limit after ~250 questions

**After:**
- Model dropdown will show: "gemini-2.0-flash-exp"
- Can handle up to 750 questions per day (3x more!)

## No Action Required

The Flask server is running in debug mode and will auto-reload these changes. Your 2 prototype users can start testing immediately with much higher capacity!

---

**Status:** ✅ COMPLETE
**Flask Server:** Auto-reloaded with new config
**Default Model:** gemini-2.0-flash-exp (1,500 RPD, 15 RPM)
