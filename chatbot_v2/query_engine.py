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
                             preferred_model: Optional[str] = None,
                             language: str = "en",
                             context_hints: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process a natural language question and return structured results"""

        start_time = time.time()

        try:
            # 1. Generate SQL from natural language
            sql_result = await self._generate_sql(question, preferred_provider, preferred_model,
                                                  language, context_hints)
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
                          preferred_model: Optional[str] = None,
                          language: str = "en",
                          context_hints: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""

        try:
            # Get database schema
            schema = self._get_database_schema()

            # Create system prompt with schema information and bilingual support
            system_prompt = self._create_system_prompt(schema, language, context_hints)
            
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
    
    def _create_system_prompt(self, schema: Dict[str, List[Dict[str, str]]],
                             language: str = "en",
                             context_hints: Optional[List[str]] = None) -> str:
        """Create system prompt with database schema and bilingual support"""

        schema_text = "Database Schema:\n\n"

        for table_name, columns in schema.items():
            schema_text += f"Table: {table_name}\n"
            for col in columns:
                pk_marker = " (PRIMARY KEY)" if col['primary_key'] else ""
                null_marker = " (NULLABLE)" if col['nullable'] else " (NOT NULL)"
                schema_text += f"  - {col['name']}: {col['type']}{pk_marker}{null_marker}\n"
            schema_text += "\n"

        # Add bilingual aliases section
        bilingual_section = self._get_bilingual_aliases_section()

        # Add business context section
        business_context = self._get_business_context_section()

        # Add context hints if provided
        hints_section = ""
        if context_hints:
            hints_section = "\nQUERY CONTEXT (from semantic analysis):\n" + "\n".join(f"- {hint}" for hint in context_hints) + "\n"

        # Get language-specific examples
        if language == "fr":
            examples = self._get_french_examples()
        else:
            examples = self._get_english_examples()

        return f"""You are an expert SQL assistant. Generate SQLite queries based on natural language questions.

{schema_text}

{bilingual_section}

{business_context}

{hints_section}

IMPORTANT RULES:
1. ONLY generate SELECT statements - never INSERT, UPDATE, DELETE, DROP, etc.
2. Use exact table and column names as shown in the schema
3. Always use proper SQLite syntax (case-sensitive)
4. For dates, use SQLite date functions like DATE('now'), datetime('now'), etc.
5. Return ONLY the SQL query - no explanations or markdown formatting
6. Use JOINs when data spans multiple tables
7. Add appropriate WHERE clauses to filter results
8. Use LIMIT to avoid returning too many rows

{examples}

Now generate a SQL query for the following question:"""

    def _get_bilingual_aliases_section(self) -> str:
        """Get bilingual column and table aliases section"""
        return """BILINGUAL COLUMN ALIASES (French → English):
  - nom → name
  - courriel → email
  - téléphone/telephone → phone
  - adresse → address
  - montant → amount
  - prix → price
  - date → date
  - statut → status
  - payé/paye → paid

BILINGUAL TABLE ALIASES (French → English):
  - utilisateurs/utilisateur/clients/client → user
  - activités/activite/activité → activity
  - passeports/passeport → passport
  - inscriptions/inscription → signup

TIME PERIOD TRANSLATIONS (French → English):
  - "ce mois" = this month = DATE(created_at) >= DATE('now', 'start of month')
  - "mois dernier"/"le mois dernier" = last month = DATE(created_at) >= DATE('now', 'start of month', '-1 month') AND DATE(created_at) < DATE('now', 'start of month')
  - "cette semaine" = this week = DATE(created_at) >= DATE('now', 'start of day', '-' || CAST(strftime('%w', 'now') AS INTEGER) || ' days')
  - "cette année"/"cette annee" = this year = DATE(created_at) >= DATE('now', 'start of year')
"""

    def _get_business_context_section(self) -> str:
        """Get business context section with Minipass-specific rules"""
        return """MINIPASS BUSINESS CONTEXT:

⚠️ CRITICAL - COMPLETE REVENUE CALCULATION (USE ALL 3 SOURCES):
  1. Passport Sales: SUM(passport.sold_amt) WHERE passport.paid = 1
  2. Other Income: SUM(income.amount) WHERE income.payment_status = 'received'
  3. Total Revenue = Passport Sales + Other Income

  ⚠️ NEVER use only passport.sold_amt - you MUST include income table!

⚠️ CRITICAL - CASH FLOW CALCULATION:
  - Cash Received = SUM(passport.sold_amt WHERE paid=1) + SUM(income.amount WHERE payment_status='received')
  - Cash Paid = SUM(expense.amount) WHERE expense.payment_status = 'paid'
  - Net Cash Flow = Cash Received - Cash Paid

  ⚠️ For "flux de trésorerie" or "cash flow" queries, you MUST use all 3 tables: passport, income, expense

Account Receivable (Money Owed to You):
  - Unpaid Passports: SUM(passport.sold_amt) WHERE passport.paid = 0
  - Pending Income: SUM(income.amount) WHERE income.payment_status = 'pending'
  - Total AR = Unpaid Passports + Pending Income

Account Payable (Money You Owe):
  - Unpaid Bills: SUM(expense.amount) WHERE expense.payment_status = 'unpaid'

Payment Status Fields:
  - passport.paid: 1 = paid, 0 = unpaid
  - income.payment_status: 'received', 'pending', 'cancelled'
  - expense.payment_status: 'paid', 'unpaid', 'cancelled'

Revenue/Cash Flow by Activity:
  - Must LEFT JOIN activity with passport, income, AND expense tables
  - Use COALESCE to handle NULL values from LEFT JOINs
  - Example structure:
    SELECT a.name,
           COALESCE(SUM(CASE WHEN p.paid = 1 THEN p.sold_amt END), 0) as passport_revenue,
           COALESCE(SUM(CASE WHEN i.payment_status = 'received' THEN i.amount END), 0) as other_income,
           COALESCE(SUM(CASE WHEN e.payment_status = 'paid' THEN e.amount END), 0) as expenses
    FROM activity a
    LEFT JOIN passport p ON p.activity_id = a.id
    LEFT JOIN income i ON i.activity_id = a.id
    LEFT JOIN expense e ON e.activity_id = a.id
    GROUP BY a.id, a.name

User Data:
  - ALWAYS join through user table for name/email
  - user.email is unique identifier
"""

    def _get_french_examples(self) -> str:
        """Get French few-shot examples"""
        return """Examples (French):

Question: "Quel est mon flux de trésorerie ce mois?"
Answer: SELECT (SELECT COALESCE(SUM(sold_amt), 0) FROM passport WHERE paid = 1 AND DATE(paid_date) >= DATE('now', 'start of month')) + (SELECT COALESCE(SUM(amount), 0) FROM income WHERE payment_status = 'received' AND DATE(payment_date) >= DATE('now', 'start of month')) - (SELECT COALESCE(SUM(amount), 0) FROM expense WHERE payment_status = 'paid' AND DATE(payment_date) >= DATE('now', 'start of month')) as flux_tresorerie

Question: "Quel est mon flux de trésorerie par activité"
Answer: SELECT a.name as activite, COALESCE(SUM(CASE WHEN p.paid = 1 THEN p.sold_amt ELSE 0 END), 0) + COALESCE(SUM(CASE WHEN i.payment_status = 'received' THEN i.amount ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN e.payment_status = 'paid' THEN e.amount ELSE 0 END), 0) as flux_tresorerie FROM activity a LEFT JOIN passport p ON p.activity_id = a.id LEFT JOIN income i ON i.activity_id = a.id LEFT JOIN expense e ON e.activity_id = a.id GROUP BY a.id, a.name ORDER BY flux_tresorerie DESC LIMIT 10

Question: "Montre-moi les utilisateurs qui n'ont pas payé"
Answer: SELECT u.name, u.email, p.sold_amt FROM passport p JOIN user u ON p.user_id = u.id WHERE p.paid = 0 LIMIT 100

Question: "Combien de revenus par activité cette année?"
Answer: SELECT a.name as activite, COALESCE(SUM(CASE WHEN p.paid = 1 THEN p.sold_amt ELSE 0 END), 0) + COALESCE(SUM(CASE WHEN i.payment_status = 'received' THEN i.amount ELSE 0 END), 0) as revenu_total FROM activity a LEFT JOIN passport p ON p.activity_id = a.id AND DATE(p.paid_date) >= DATE('now', 'start of year') LEFT JOIN income i ON i.activity_id = a.id AND DATE(i.payment_date) >= DATE('now', 'start of year') GROUP BY a.id, a.name ORDER BY revenu_total DESC

Question: "Quelles activités génèrent le plus de revenus?"
Answer: SELECT a.name as activite, COALESCE(SUM(CASE WHEN p.paid = 1 THEN p.sold_amt ELSE 0 END), 0) + COALESCE(SUM(CASE WHEN i.payment_status = 'received' THEN i.amount ELSE 0 END), 0) as revenu_total FROM activity a LEFT JOIN passport p ON p.activity_id = a.id LEFT JOIN income i ON i.activity_id = a.id GROUP BY a.id, a.name ORDER BY revenu_total DESC LIMIT 10

Question: "Montre-moi le revenu de ce mois"
Answer: SELECT (SELECT COALESCE(SUM(sold_amt), 0) FROM passport WHERE paid = 1 AND DATE(paid_date) >= DATE('now', 'start of month')) + (SELECT COALESCE(SUM(amount), 0) FROM income WHERE payment_status = 'received' AND DATE(payment_date) >= DATE('now', 'start of month')) as revenu_total
"""

    def _get_english_examples(self) -> str:
        """Get English few-shot examples"""
        return """Examples (English):

Question: "Show me all users"
Answer: SELECT * FROM user LIMIT 100

Question: "Find unpaid passports"
Answer: SELECT u.name, u.email, a.name as activity_name FROM passport p JOIN user u ON p.user_id = u.id JOIN activity a ON p.activity_id = a.id WHERE p.paid = 0 LIMIT 100

Question: "What is our total revenue this month?"
Answer: SELECT (SELECT COALESCE(SUM(sold_amt), 0) FROM passport WHERE paid = 1 AND DATE(paid_date) >= DATE('now', 'start of month')) + (SELECT COALESCE(SUM(amount), 0) FROM income WHERE payment_status = 'received' AND DATE(payment_date) >= DATE('now', 'start of month')) as total_revenue

Question: "What is our cash flow by activity?"
Answer: SELECT a.name as activity, COALESCE(SUM(CASE WHEN p.paid = 1 THEN p.sold_amt ELSE 0 END), 0) + COALESCE(SUM(CASE WHEN i.payment_status = 'received' THEN i.amount ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN e.payment_status = 'paid' THEN e.amount ELSE 0 END), 0) as net_cash_flow FROM activity a LEFT JOIN passport p ON p.activity_id = a.id LEFT JOIN income i ON i.activity_id = a.id LEFT JOIN expense e ON e.activity_id = a.id GROUP BY a.id, a.name ORDER BY net_cash_flow DESC LIMIT 10

Question: "Show users who didn't pay for Golf 2025"
Answer: SELECT u.name, u.email, p.sold_amt FROM passport p JOIN user u ON p.user_id = u.id JOIN activity a ON p.activity_id = a.id WHERE a.name LIKE '%Golf%' AND a.name LIKE '%2025%' AND p.paid = 0 LIMIT 100
"""

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
        
        # PII masking disabled - only admins use this chatbot
        # They need full email addresses to contact users

        # Suggest chart type based on data structure
        chart_suggestion = self._suggest_chart_type(columns, data, question)

        return {
            'columns': columns,
            'rows': rows,  # Return unmasked rows
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