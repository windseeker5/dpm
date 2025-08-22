#!/usr/bin/env python
"""Test the chatbot functionality"""

import requests
import json

def test_chatbot():
    url = "http://127.0.0.1:8890/chatbot/ask"
    
    questions = [
        "What is our total revenue?",
        "How many users have signed up?",
        "What are the most popular activities?",
        "Show me pending signups",
        "How many active passports do we have?"
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        
        payload = {
            "question": question,
            "conversation_id": "test-123",
            "provider": "database_query",
            "model": "database-query"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"Answer: {data.get('answer', 'No answer')}")
                    if data.get('sql'):
                        print(f"\nSQL Query:\n{data.get('sql')}")
                    if data.get('rows'):
                        print(f"\nResults ({data.get('row_count', 0)} rows):")
                        for row in data.get('rows', [])[:5]:  # Show first 5 rows
                            print(f"  {row}")
                else:
                    print(f"Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"HTTP Error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chatbot()