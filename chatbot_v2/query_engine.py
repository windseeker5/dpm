"""
Query Engine for AI Analytics Chatbot
Handles SQL generation, execution, and result formatting
"""
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from flask import current_app

from .ai_providers import provider_manager, AIRequest
from .security import QueryExecutor, PIIDetector
from .config import MAX_QUERY_TIMEOUT_SECONDS


class QueryEngine:
    """Main query engine that orchestrates AI and database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.executor = QueryExecutor(db_path)
        self.schema_cache = None
        self.schema_cache_time = None
    
    async def process_question(self, question: str, admin_email: str, 
                             preferred_provider: Optional[str] = None,
                             preferred_model: Optional[str] = None) -> Dict[str, Any]:
        """Process a natural language question and return structured results"""
        
        start_time = time.time()
        
        try:
            # 1. Generate SQL from natural language
            sql_result = await self._generate_sql(question, preferred_provider, preferred_model)
            if not sql_result['success']:
                return sql_result
            
            # 2. Execute the SQL query
            query_result = self.executor.execute_query(sql_result['sql'])
            
            # 3. Format and enrich the results
            formatted_result = self._format_results(query_result, question)
            
            # 4. Calculate total processing time
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # 5. Combine all results
            final_result = {
                'success': query_result['success'],
                'question': question,
                'sql': sql_result['sql'],
                'ai_provider': sql_result.get('ai_provider'),
                'ai_model': sql_result.get('ai_model'),
                'tokens_used': sql_result.get('tokens_used', 0),
                'cost_cents': sql_result.get('cost_cents', 0),
                'processing_time_ms': total_time_ms,
                'admin_email': admin_email,
                **formatted_result
            }
            
            # 6. Log the query for monitoring
            self._log_query(final_result)
            
            return final_result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Query processing failed: {str(e)}",
                'question': question,
                'admin_email': admin_email,
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    async def _generate_sql(self, question: str, preferred_provider: Optional[str] = None,
                          preferred_model: Optional[str] = None) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        
        try:
            # Get database schema
            schema = self._get_database_schema()
            
            # Create system prompt with schema information
            system_prompt = self._create_system_prompt(schema)
            
            # Create AI request
            ai_request = AIRequest(
                prompt=question,
                system_prompt=system_prompt,
                model=preferred_model or 'dolphin-mistral:latest',
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=500,   # SQL queries shouldn't be too long
                timeout_seconds=MAX_QUERY_TIMEOUT_SECONDS
            )
            
            # Generate SQL using AI
            ai_response = await provider_manager.generate(ai_request, preferred_provider)
            
            if ai_response.error:
                return {
                    'success': False,
                    'error': f"AI generation failed: {ai_response.error}",
                    'ai_provider': ai_response.provider
                }
            
            # Clean and validate the generated SQL
            sql = self._clean_generated_sql(ai_response.content)
            print(f"🤖 Generated SQL: {sql}")
            
            return {
                'success': True,
                'sql': sql,
                'ai_provider': ai_response.provider,
                'ai_model': ai_response.model,
                'tokens_used': ai_response.tokens_used,
                'cost_cents': ai_response.cost_cents,
                'response_time_ms': ai_response.response_time_ms
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"SQL generation error: {str(e)}"
            }
    
    def _get_database_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """Get database schema information with caching"""
        
        # Return cached schema if still valid (cache for 1 hour)
        if (self.schema_cache and self.schema_cache_time and 
            (datetime.now() - self.schema_cache_time).seconds < 3600):
            return self.schema_cache
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            schema = {}
            
            # Get all table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # Get column information for each table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema[table_name] = [
                    {
                        'name': col[1],
                        'type': col[2],
                        'nullable': not col[3],
                        'primary_key': bool(col[5])
                    }
                    for col in columns
                ]
            
            conn.close()
            
            # Cache the schema
            self.schema_cache = schema
            self.schema_cache_time = datetime.now()
            
            print(f"✅ Schema fetched successfully: {len(schema)} tables")
            return schema
            
        except Exception as e:
            # Return a basic schema if we can't fetch the real one
            current_app.logger.error(f"Failed to fetch database schema from {self.db_path}: {e}")
            print(f"❌ Schema fetch failed: {e}")
            return self._get_fallback_schema()
    
    def _get_fallback_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """Fallback schema when we can't fetch from database"""
        return {
            'user': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'name', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False},
                {'name': 'email', 'type': 'VARCHAR(100)', 'nullable': True, 'primary_key': False},
                {'name': 'phone_number', 'type': 'VARCHAR(20)', 'nullable': True, 'primary_key': False}
            ],
            'activity': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'name', 'type': 'VARCHAR(150)', 'nullable': False, 'primary_key': False},
                {'name': 'type', 'type': 'VARCHAR(50)', 'nullable': True, 'primary_key': False},
                {'name': 'description', 'type': 'TEXT', 'nullable': True, 'primary_key': False},
                {'name': 'start_date', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'end_date', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'status', 'type': 'VARCHAR(50)', 'nullable': True, 'primary_key': False},
                {'name': 'created_dt', 'type': 'DATETIME', 'nullable': True, 'primary_key': False}
            ],
            'passport': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'pass_code', 'type': 'VARCHAR(16)', 'nullable': False, 'primary_key': False},
                {'name': 'user_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'activity_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'passport_type_id', 'type': 'INTEGER', 'nullable': True, 'primary_key': False},
                {'name': 'passport_type_name', 'type': 'VARCHAR(100)', 'nullable': True, 'primary_key': False},
                {'name': 'sold_amt', 'type': 'FLOAT', 'nullable': True, 'primary_key': False},
                {'name': 'uses_remaining', 'type': 'INTEGER', 'nullable': True, 'primary_key': False},
                {'name': 'paid', 'type': 'BOOLEAN', 'nullable': True, 'primary_key': False},
                {'name': 'paid_date', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'created_dt', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'notes', 'type': 'TEXT', 'nullable': True, 'primary_key': False}
            ],
            'passport_type': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'activity_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'name', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False},
                {'name': 'type', 'type': 'VARCHAR(50)', 'nullable': False, 'primary_key': False},
                {'name': 'price_per_user', 'type': 'FLOAT', 'nullable': True, 'primary_key': False},
                {'name': 'sessions_included', 'type': 'INTEGER', 'nullable': True, 'primary_key': False},
                {'name': 'target_revenue', 'type': 'FLOAT', 'nullable': True, 'primary_key': False},
                {'name': 'status', 'type': 'VARCHAR(50)', 'nullable': True, 'primary_key': False},
                {'name': 'created_dt', 'type': 'DATETIME', 'nullable': True, 'primary_key': False}
            ],
            'signup': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'user_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'activity_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'passport_type_id', 'type': 'INTEGER', 'nullable': True, 'primary_key': False},
                {'name': 'subject', 'type': 'VARCHAR(200)', 'nullable': True, 'primary_key': False},
                {'name': 'signed_up_at', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'paid', 'type': 'BOOLEAN', 'nullable': True, 'primary_key': False},
                {'name': 'paid_at', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'passport_id', 'type': 'INTEGER', 'nullable': True, 'primary_key': False},
                {'name': 'status', 'type': 'VARCHAR(50)', 'nullable': True, 'primary_key': False}
            ],
            'expense': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'activity_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'date', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'category', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False},
                {'name': 'amount', 'type': 'FLOAT', 'nullable': False, 'primary_key': False},
                {'name': 'description', 'type': 'TEXT', 'nullable': True, 'primary_key': False},
                {'name': 'created_by', 'type': 'VARCHAR(100)', 'nullable': True, 'primary_key': False}
            ],
            'income': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'activity_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': False},
                {'name': 'date', 'type': 'DATETIME', 'nullable': True, 'primary_key': False},
                {'name': 'category', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False},
                {'name': 'amount', 'type': 'FLOAT', 'nullable': False, 'primary_key': False},
                {'name': 'note', 'type': 'TEXT', 'nullable': True, 'primary_key': False},
                {'name': 'created_by', 'type': 'VARCHAR(100)', 'nullable': True, 'primary_key': False}
            ],
            'admin': [
                {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
                {'name': 'email', 'type': 'VARCHAR(100)', 'nullable': False, 'primary_key': False}
            ]
        }
    
    def _create_system_prompt(self, schema: Dict[str, List[Dict[str, str]]]) -> str:
        """Create system prompt with database schema"""
        
        schema_text = "Database Schema:\n\n"
        
        for table_name, columns in schema.items():
            schema_text += f"Table: {table_name}\n"
            for col in columns:
                pk_marker = " (PRIMARY KEY)" if col['primary_key'] else ""
                null_marker = " (NULLABLE)" if col['nullable'] else " (NOT NULL)"
                schema_text += f"  - {col['name']}: {col['type']}{pk_marker}{null_marker}\n"
            schema_text += "\n"
        
        return f"""You are an expert SQL assistant. Generate SQLite queries based on natural language questions.

{schema_text}

IMPORTANT RULES:
1. ONLY generate SELECT statements - never INSERT, UPDATE, DELETE, DROP, etc.
2. Use exact table and column names as shown in the schema
3. Always use proper SQLite syntax (case-sensitive)
4. For dates, use SQLite date functions like DATE('now'), datetime('now'), etc.
5. Return ONLY the SQL query - no explanations or markdown formatting
6. Use JOINs when data spans multiple tables
7. Add appropriate WHERE clauses to filter results
8. Use LIMIT to avoid returning too many rows

KEY RELATIONSHIPS:
- Revenue/Price data: passport.sold_amt (actual revenue) or passport_type.price_per_user (listed price)
- Financial data: expense.amount, income.amount
- User data: Always join through user table
- Payment status: passport.paid (boolean), signup.paid (boolean)

Examples:
Question: "Show me all users"
Answer: SELECT * FROM user LIMIT 100

Question: "Find unpaid passports"  
Answer: SELECT u.name, u.email, a.name as activity_name FROM passport p JOIN user u ON p.user_id = u.id JOIN activity a ON p.activity_id = a.id WHERE p.paid = 0 LIMIT 100

Question: "What is our total revenue this month?"
Answer: SELECT SUM(p.sold_amt) as total_revenue FROM passport p WHERE p.paid = 1 AND DATE(p.paid_date) >= DATE('now', 'start of month')

Question: "Show users who didn't pay for Golf 2025"
Answer: SELECT u.name, u.email, p.sold_amt FROM passport p JOIN user u ON p.user_id = u.id JOIN activity a ON p.activity_id = a.id WHERE a.name LIKE '%Golf%' AND a.name LIKE '%2025%' AND p.paid = 0 LIMIT 100

Now generate a SQL query for the following question:"""
    
    def _clean_generated_sql(self, raw_sql: str) -> str:
        """Clean and normalize generated SQL"""
        
        sql = raw_sql.strip()
        
        # Remove common AI formatting
        if sql.startswith('```sql'):
            sql = sql[6:]
        if sql.startswith('```'):
            sql = sql[3:]
        if sql.endswith('```'):
            sql = sql[:-3]
        
        # Remove extra whitespace
        sql = ' '.join(sql.split())
        
        # Ensure it ends properly (no semicolon)
        sql = sql.rstrip(';')
        
        return sql
    
    def _format_results(self, query_result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Format query results for display"""
        
        if not query_result['success']:
            return {
                'error': query_result.get('error', 'Unknown query error'),
                'columns': [],
                'rows': [],
                'row_count': 0,
                'chart_suggestion': None
            }
        
        data = query_result.get('data', [])
        columns = query_result.get('columns', [])
        
        # Convert data to list of lists for easier display
        rows = []
        for row_dict in data:
            row = [row_dict.get(col, '') for col in columns]
            rows.append(row)
        
        # Check for PII and mask if needed
        masked_rows = []
        for row in rows:
            masked_row = []
            for cell in row:
                if isinstance(cell, str):
                    masked_cell = PIIDetector.mask_pii(str(cell))
                    masked_row.append(masked_cell)
                else:
                    masked_row.append(cell)
            masked_rows.append(masked_row)
        
        # Suggest chart type based on data structure
        chart_suggestion = self._suggest_chart_type(columns, data, question)
        
        return {
            'columns': columns,
            'rows': masked_rows,
            'row_count': len(data),
            'chart_suggestion': chart_suggestion,
            'sql_executed': query_result.get('sql_executed')
        }
    
    def _suggest_chart_type(self, columns: List[str], data: List[Dict], question: str) -> Optional[Dict[str, Any]]:
        """Suggest appropriate chart type based on data structure"""
        
        if not data or len(columns) < 2:
            return None
        
        # Check if we have numeric data for charting
        numeric_columns = []
        for col in columns:
            if any(isinstance(row.get(col), (int, float)) for row in data):
                numeric_columns.append(col)
        
        if len(numeric_columns) == 0:
            return None
        
        # Simple chart suggestions based on question keywords
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['trend', 'over time', 'by month', 'by year', 'timeline']):
            return {
                'type': 'line',
                'x_column': columns[0],
                'y_column': numeric_columns[0],
                'title': 'Trend Over Time'
            }
        elif any(word in question_lower for word in ['compare', 'by activity', 'by type', 'breakdown']):
            return {
                'type': 'bar',
                'x_column': columns[0],
                'y_column': numeric_columns[0],
                'title': 'Comparison Chart'
            }
        elif len(data) <= 10 and len(numeric_columns) == 1:
            return {
                'type': 'pie',
                'label_column': columns[0],
                'value_column': numeric_columns[0],
                'title': 'Distribution Chart'
            }
        
        return None
    
    def _log_query(self, result: Dict[str, Any]):
        """Log query execution for monitoring"""
        try:
            from models import QueryLog, db
            
            log_entry = QueryLog(
                admin_email=result.get('admin_email', 'unknown'),
                original_question=result.get('question', ''),
                generated_sql=result.get('sql', ''),
                execution_status='success' if result.get('success') else 'error',
                execution_time_ms=result.get('processing_time_ms', 0),
                rows_returned=result.get('row_count', 0),
                error_message=result.get('error'),
                ai_provider=result.get('ai_provider'),
                ai_model=result.get('ai_model'),
                tokens_used=result.get('tokens_used', 0),
                cost_cents=result.get('cost_cents', 0)
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Failed to log query: {e}")


# Helper function to create query engine instance
def create_query_engine(db_path: str) -> QueryEngine:
    """Create and configure a query engine instance"""
    return QueryEngine(db_path)