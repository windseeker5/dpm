"""
Mock AI Provider for Testing
Provides simulated responses when real AI providers are unavailable
"""
import time
import re
from typing import Dict, Any
from datetime import datetime

from ..ai_providers import AIProvider, AIRequest, AIResponse


class MockProvider(AIProvider):
    """Mock AI provider for testing and fallback purposes"""
    
    def __init__(self):
        super().__init__("mock", {"type": "testing"})
        self.is_available = True
        self.last_check = datetime.now()
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate mock SQL response based on simple patterns"""
        start_time = time.time()
        
        try:
            # Simple pattern matching to generate SQL
            question = request.prompt.lower()
            sql = self._generate_mock_sql(question)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                content=sql,
                model=request.model or "mock-model",
                provider=self.name,
                tokens_used=len(request.prompt.split()),
                cost_cents=0,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=request.model,
                provider=self.name,
                error=f"Mock provider error: {str(e)}"
            )
    
    def _generate_mock_sql(self, question: str) -> str:
        """Generate basic SQL based on question patterns"""
        
        # Revenue/money related queries
        if any(word in question for word in ['revenue', 'money', 'income', 'paid', 'sales']):
            if 'month' in question:
                return "SELECT SUM(p.sold_amt) as total_revenue FROM passport p WHERE p.paid = 1 AND DATE(p.paid_date) >= DATE('now', 'start of month')"
            elif 'year' in question:
                return "SELECT SUM(p.sold_amt) as total_revenue FROM passport p WHERE p.paid = 1 AND DATE(p.paid_date) >= DATE('now', 'start of year')"
            else:
                return "SELECT SUM(p.sold_amt) as total_revenue FROM passport p WHERE p.paid = 1"
        
        # User related queries
        elif any(word in question for word in ['user', 'users', 'people', 'customer']):
            if 'unpaid' in question:
                return "SELECT u.name, u.email FROM passport p JOIN user u ON p.user_id = u.id WHERE p.paid = 0 LIMIT 100"
            elif 'new' in question or 'recent' in question:
                return "SELECT u.name, u.email, u.created_dt FROM user u ORDER BY u.created_dt DESC LIMIT 50"
            else:
                return "SELECT u.name, u.email FROM user u LIMIT 100"
        
        # Activity related queries
        elif any(word in question for word in ['activity', 'activities', 'class', 'course']):
            if 'popular' in question or 'most' in question:
                return "SELECT a.name, COUNT(s.id) as signup_count FROM activity a LEFT JOIN signup s ON a.id = s.activity_id GROUP BY a.id, a.name ORDER BY signup_count DESC LIMIT 10"
            else:
                return "SELECT a.name, a.type, a.status FROM activity a WHERE a.active = 1 LIMIT 50"
        
        # Signup related queries
        elif any(word in question for word in ['signup', 'signups', 'registration']):
            return "SELECT u.name, a.name as activity_name, s.signed_up_at FROM signup s JOIN user u ON s.user_id = u.id JOIN activity a ON s.activity_id = a.id ORDER BY s.signed_up_at DESC LIMIT 100"
        
        # Growth/trend related queries
        elif any(word in question for word in ['growth', 'trend', 'over time']):
            return "SELECT DATE(u.created_dt) as date, COUNT(*) as new_users FROM user u GROUP BY DATE(u.created_dt) ORDER BY date DESC LIMIT 30"
        
        # Default query
        else:
            return "SELECT COUNT(*) as total_users FROM user"
    
    def check_availability(self) -> bool:
        """Mock provider is always available"""
        self.is_available = True
        self.last_check = datetime.now()
        return True
    
    def get_available_models(self) -> list[str]:
        """Return mock models"""
        return ["mock-sql-assistant", "mock-data-analyst"]
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> int:
        """Mock provider is free"""
        return 0


def create_mock_provider() -> MockProvider:
    """Create and configure a mock provider"""
    return MockProvider()