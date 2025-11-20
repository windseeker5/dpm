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
            log_id = self._log_query(final_result)
            if log_id:
                final_result['query_log_id'] = log_id

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

            # Create simple system prompt with schema
            system_prompt = self._create_system_prompt(schema)

            # Create AI request
            final_model = preferred_model or 'dolphin-mistral:latest'
            print(f"🔍 QUERY_ENGINE DEBUG: Creating AIRequest with model='{final_model}', preferred_provider='{preferred_provider}'")

            ai_request = AIRequest(
                prompt=question,
                system_prompt=system_prompt,
                model=final_model,
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=500,   # SQL queries shouldn't be too long
                timeout_seconds=MAX_QUERY_TIMEOUT_SECONDS
            )

            # Generate SQL using AI
            print(f"🚀 QUERY_ENGINE DEBUG: Calling provider_manager.generate(preferred_provider='{preferred_provider}', model='{final_model}')")
            ai_response = await provider_manager.generate(ai_request, preferred_provider)
            print(f"📥 QUERY_ENGINE DEBUG: Got response from provider='{ai_response.provider}', model='{ai_response.model}', error='{ai_response.error}'")
            
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

            # Get all table and view names
            cursor.execute("""
                SELECT name, type FROM sqlite_master
                WHERE (type='table' OR type='view') AND name NOT LIKE 'sqlite_%'
                ORDER BY type DESC, name
            """)

            objects = cursor.fetchall()

            for (object_name, object_type) in objects:
                # Get column information for each table/view
                cursor.execute(f"PRAGMA table_info({object_name})")
                columns = cursor.fetchall()

                schema[object_name] = [
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
        """Create minimal system prompt with just schema and basic rules"""

        schema_text = "DATABASE SCHEMA:\n\n"

        for table_name, columns in schema.items():
            schema_text += f"Table: {table_name}\n"
            for col in columns:
                pk_marker = " (PRIMARY KEY)" if col['primary_key'] else ""
                null_marker = " (NULLABLE)" if col['nullable'] else " (NOT NULL)"
                schema_text += f"  - {col['name']}: {col['type']}{pk_marker}{null_marker}\n"
            schema_text += "\n"

        return f"""You are a SQL query generator for a Minipass activity management platform.

{schema_text}

⚠️ CRITICAL: USE VIEWS FOR ALL FINANCIAL QUERIES ⚠️

MANDATORY RULES - DO NOT IGNORE:
1. For ANY question about revenue, income, sales → USE monthly_financial_summary
2. For ANY question about cash flow, profit, net income → USE monthly_financial_summary
3. For ANY question about AR, AP, unpaid invoices → USE monthly_transactions_detail
4. NEVER use passport, income, expense tables directly for financial queries
5. These views are optimized and correct - raw tables will give WRONG results

View: monthly_financial_summary (USE FOR: revenue, cash flow, profit, totals)
Columns: month, account (activity name), passport_sales, other_income, cash_received, cash_paid, net_cash_flow, accounts_receivable, accounts_payable, total_revenue, total_expenses, net_income
⚠️ IMPORTANT: This view returns one row per activity per month. For TOTALS, you MUST use SUM() and GROUP BY month!
Examples:
  - "revenue this month" → SELECT SUM(total_revenue) FROM monthly_financial_summary WHERE month = strftime('%Y-%m', 'now')
  - "cash flow" → SELECT month, SUM(net_cash_flow) as total_cash_flow FROM monthly_financial_summary GROUP BY month ORDER BY month DESC
  - "cash flow by activity" → SELECT month, account, net_cash_flow FROM monthly_financial_summary ORDER BY month DESC
  - "profit" → SELECT month, SUM(net_income) as total_profit FROM monthly_financial_summary GROUP BY month ORDER BY month DESC

View: monthly_transactions_detail (USE FOR: transaction details, AR/AP, ledger)
Columns: month, project, transaction_type, account, customer, amount, payment_status
Examples:
  - "unpaid invoices" → SELECT * FROM monthly_transactions_detail WHERE payment_status = 'Unpaid (AR)'
  - "accounts receivable" → SELECT * FROM monthly_transactions_detail WHERE payment_status = 'Unpaid (AR)'

CRITICAL BUSINESS RULES:
- Total Revenue = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount) - SUM(expense.amount)
- passport.sold_amt is the actual revenue received (what customer paid)
- passport_type.price_per_user is the listed price (may differ from actual amount paid)
- For cash flow or revenue queries, use passport.sold_amt (not price_per_user)

QUERY RULES:
1. Generate SQLite-compatible SELECT queries only (no INSERT, UPDATE, DELETE, DROP)
2. Return maximum 100 rows (use LIMIT 100)
3. Use proper JOINs when querying across tables
4. Handle both French and English questions naturally
5. Include relevant columns in results (names, emails, amounts, dates)
6. For dates, use SQLite date functions: DATE('now'), DATE('now', 'start of month'), etc.
7. Return ONLY the SQL query - no explanations or markdown formatting

Generate the SQL query for the following question:"""

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

        # Fix corrupted SQL - sometimes AI generates "ite SELECT" or "SQLite SELECT" instead of "SELECT"
        # Extract from "SELECT" onwards (case-insensitive)
        import re
        select_match = re.search(r'\b(SELECT)\b', sql, re.IGNORECASE)
        if select_match:
            # Extract everything from SELECT onwards
            sql = sql[select_match.start():]

        # Ensure it ends properly (no semicolon)
        sql = sql.rstrip(';')

        return sql

    def _format_column_name(self, column: str) -> str:
        """Format column name for display - convert snake_case to Title Case"""

        # Handle SQL aggregate functions like SUM(net_cash_flow)
        if '(' in column and ')' in column:
            # Extract function and column name
            import re
            match = re.match(r'(\w+)\((.+)\)', column)
            if match:
                func = match.group(1).upper()
                col_name = match.group(2)

                # Format the column name inside
                formatted_col = self._format_column_name(col_name)

                # Map function names to friendly names
                func_map = {
                    'SUM': 'Total',
                    'AVG': 'Average',
                    'COUNT': 'Count',
                    'MAX': 'Maximum',
                    'MIN': 'Minimum'
                }
                friendly_func = func_map.get(func, func.title())

                return f"{formatted_col} ({friendly_func})"

        # Convert snake_case to Title Case
        # Split by underscore
        words = column.replace('_', ' ').split()

        # Capitalize each word
        formatted_words = []
        for word in words:
            # Keep certain words lowercase unless they're the first word
            lowercase_words = {'of', 'and', 'or', 'the', 'in', 'on', 'at', 'to', 'for'}
            if word.lower() in lowercase_words and formatted_words:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.capitalize())

        return ' '.join(formatted_words)

    def _is_money_column(self, column: str) -> bool:
        """Detect if a column represents money/currency values"""

        money_keywords = [
            'revenue', 'cash', 'flow', 'payment', 'cost', 'price',
            'amount', 'total', 'sum', 'income', 'expense', 'balance',
            'fee', 'charge', 'paid', 'owing', 'receivable', 'payable'
        ]

        column_lower = column.lower()
        return any(keyword in column_lower for keyword in money_keywords)

    def _format_cell_value(self, value, column: str) -> str:
        """Format cell value based on type and column context"""

        # Handle None/empty values
        if value is None or value == '':
            return ''

        # Detect money columns and format as currency
        if self._is_money_column(column):
            try:
                # Convert to float and format as currency
                amount = float(value)
                return f"${amount:,.2f}"
            except (ValueError, TypeError):
                pass

        # Format floating point numbers (round to 2 decimals)
        if isinstance(value, float):
            # Check if it's essentially an integer
            if value == int(value):
                return f"{int(value):,}"
            else:
                return f"{value:.2f}"

        # Format large integers with comma separators
        if isinstance(value, int):
            return f"{value:,}"

        # Return as string for everything else
        return str(value)

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

        # Format column names for display
        formatted_columns = [self._format_column_name(col) for col in columns]

        # Convert data to list of lists with formatted values
        rows = []
        for row_dict in data:
            formatted_row = []
            for col in columns:
                raw_value = row_dict.get(col, '')
                formatted_value = self._format_cell_value(raw_value, col)
                formatted_row.append(formatted_value)
            rows.append(formatted_row)

        # PII masking disabled - only admins use this chatbot
        # They need full email addresses to contact users

        # Suggest chart type based on data structure
        chart_suggestion = self._suggest_chart_type(columns, data, question)

        return {
            'columns': formatted_columns,  # Return formatted column names
            'rows': rows,  # Return formatted rows
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
    
    def _log_query(self, result: Dict[str, Any]) -> Optional[int]:
        """Log query execution for monitoring and return log entry ID"""
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

            return log_entry.id

        except Exception as e:
            current_app.logger.error(f"Failed to log query: {e}")
            return None

    @staticmethod
    def update_query_log_answer(log_id: int, answer: str):
        """Update query log entry with the AI's natural language answer"""
        try:
            from models import QueryLog, db

            log_entry = QueryLog.query.get(log_id)
            if log_entry:
                log_entry.ai_answer = answer
                db.session.commit()
            else:
                current_app.logger.warning(f"Query log entry {log_id} not found")

        except Exception as e:
            current_app.logger.error(f"Failed to update query log answer: {e}")


# Helper function to create query engine instance
def create_query_engine(db_path: str) -> QueryEngine:
    """Create and configure a query engine instance"""
    return QueryEngine(db_path)