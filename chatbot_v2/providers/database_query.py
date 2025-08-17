"""
Database Query Provider - Provides actual database queries with pattern matching
"""
import time
import re
from typing import Dict, Any
from datetime import datetime
import sqlite3
import json

from ..ai_providers import AIProvider, AIRequest, AIResponse


class DatabaseQueryProvider(AIProvider):
    """Provider that generates real SQL queries based on patterns"""
    
    def __init__(self, db_path="/home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db"):
        super().__init__("database_query", {"type": "pattern_based"})
        self.is_available = True
        self.last_check = datetime.now()
        self.db_path = db_path
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate SQL response based on question patterns"""
        start_time = time.time()
        
        try:
            question = request.prompt.lower()
            
            # Generate SQL based on patterns
            sql, explanation = self._generate_sql_from_pattern(question)
            
            # Execute the query
            result = self._execute_query(sql)
            
            # Format response
            if result['success']:
                response_content = f"{explanation}\n\nSQL: {sql}\n\nResult: {json.dumps(result['data'], indent=2)}"
            else:
                response_content = f"Error executing query: {result.get('error', 'Unknown error')}"
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                content=response_content,
                model="database-query",
                provider=self.name,
                tokens_used=len(request.prompt.split()),
                cost_cents=0,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model="database-query",
                provider=self.name,
                error=f"Database query error: {str(e)}"
            )
    
    def _generate_sql_from_pattern(self, question: str) -> tuple:
        """Generate SQL based on question patterns"""
        
        # Revenue queries
        if 'revenue' in question or 'income' in question or 'money' in question:
            if 'total' in question or 'all' in question:
                return (
                    "SELECT SUM(sold_amt) as total_revenue, COUNT(*) as total_passports FROM passport WHERE paid = 1",
                    "Calculating total revenue from all paid passports"
                )
            elif 'month' in question or 'monthly' in question:
                return (
                    "SELECT strftime('%Y-%m', paid_date) as month, SUM(sold_amt) as revenue, COUNT(*) as passports FROM passport WHERE paid = 1 GROUP BY month ORDER BY month DESC LIMIT 12",
                    "Monthly revenue breakdown for the last 12 months"
                )
            elif 'activity' in question:
                return (
                    """SELECT a.name as activity, COUNT(p.id) as passports_sold, SUM(p.sold_amt) as revenue 
                       FROM activity a 
                       LEFT JOIN passport_type pt ON pt.activity_id = a.id 
                       LEFT JOIN passport p ON p.passport_type_id = pt.id AND p.paid = 1
                       GROUP BY a.id, a.name 
                       ORDER BY revenue DESC""",
                    "Revenue breakdown by activity"
                )
        
        # User/signup queries
        elif 'user' in question or 'signup' in question or 'registration' in question:
            if 'pending' in question or 'unpaid' in question:
                return (
                    """SELECT s.id, s.fname || ' ' || s.lname as name, s.email, a.name as activity
                       FROM signup s
                       JOIN activity a ON s.activity_id = a.id
                       WHERE s.paid = 0
                       ORDER BY s.created_at DESC""",
                    "List of pending/unpaid signups"
                )
            elif 'count' in question or 'total' in question or 'how many' in question:
                return (
                    """SELECT 
                       COUNT(DISTINCT CASE WHEN paid = 1 THEN id END) as paid_signups,
                       COUNT(DISTINCT CASE WHEN paid = 0 THEN id END) as pending_signups,
                       COUNT(*) as total_signups
                       FROM signup""",
                    "Signup statistics"
                )
            elif 'recent' in question or 'latest' in question or 'new' in question:
                return (
                    """SELECT id, fname || ' ' || lname as name, email, 
                       datetime(created_at) as signed_up_at,
                       CASE WHEN paid = 1 THEN 'Paid' ELSE 'Pending' END as status
                       FROM signup 
                       ORDER BY created_at DESC 
                       LIMIT 10""",
                    "10 most recent signups"
                )
        
        # Activity queries
        elif 'activity' in question or 'activities' in question or 'event' in question:
            if 'popular' in question or 'most' in question:
                return (
                    """SELECT a.name, COUNT(s.id) as signups, 
                       COUNT(CASE WHEN s.paid = 1 THEN 1 END) as paid_signups
                       FROM activity a
                       LEFT JOIN signup s ON s.activity_id = a.id
                       WHERE a.status = 'active'
                       GROUP BY a.id, a.name
                       ORDER BY signups DESC""",
                    "Activities ranked by popularity (number of signups)"
                )
            elif 'active' in question or 'current' in question:
                return (
                    """SELECT name, description, 
                       datetime(start_date) as starts_at,
                       capacity
                       FROM activity 
                       WHERE active = 1
                       ORDER BY start_date""",
                    "Currently active activities"
                )
        
        # Passport queries
        elif 'passport' in question or 'pass' in question or 'ticket' in question:
            if 'active' in question or 'valid' in question:
                return (
                    """SELECT COUNT(*) as active_passports,
                       SUM(uses_remaining) as remaining_sessions
                       FROM passport 
                       WHERE paid = 1 AND uses_remaining > 0""",
                    "Active passports and remaining sessions"
                )
            elif 'redeemed' in question or 'used' in question:
                return (
                    """SELECT p.pass_code, u.fname || ' ' || u.lname as owner,
                       p.uses_remaining,
                       datetime(p.created_dt) as created
                       FROM passport p
                       JOIN user u ON p.user_id = u.id
                       WHERE p.uses_remaining IS NOT NULL
                       ORDER BY p.last_redeemed DESC
                       LIMIT 20""",
                    "Recently redeemed passports"
                )
        
        # Default query
        else:
            return (
                """SELECT 
                   (SELECT COUNT(*) FROM activity WHERE active = 1) as active_activities,
                   (SELECT COUNT(*) FROM signup) as total_signups,
                   (SELECT COUNT(*) FROM passport WHERE paid = 1) as paid_passports,
                   (SELECT SUM(sold_amt) FROM passport WHERE paid = 1) as total_revenue""",
                "Overview of system statistics"
            )
    
    def _execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            data = []
            for row in rows:
                data.append(dict(row))
            
            conn.close()
            
            return {
                'success': True,
                'data': data,
                'row_count': len(data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def check_availability(self) -> bool:
        """Check if database is available"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False
    
    def get_models(self) -> list:
        """Return available models"""
        return ["database-query"]
    
    def get_available_models(self) -> list:
        """Return available models (required by base class)"""
        return ["database-query"]
    
    def calculate_cost(self, tokens: int, model: str = None) -> int:
        """Calculate cost in cents (always 0 for database queries)"""
        return 0


def create_database_query_provider(db_path=None):
    """Factory function to create database query provider"""
    if db_path:
        return DatabaseQueryProvider(db_path)
    return DatabaseQueryProvider()