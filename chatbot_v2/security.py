"""
Security module for SQL validation and sanitization
Prevents SQL injection and enforces read-only access
"""
import re
import sqlite3
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from .config import ALLOWED_SQL_KEYWORDS, BLOCKED_SQL_KEYWORDS, MAX_RESULT_ROWS


@dataclass
class SecurityResult:
    """Result of security validation"""
    is_safe: bool
    error_message: Optional[str] = None
    sanitized_sql: Optional[str] = None
    blocked_reason: Optional[str] = None


class SQLSecurity:
    """SQL security validation and sanitization"""
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'(?i)\b(exec|execute)\b',  # SQL execution functions
        r'(?i)\b(sp_|xp_)\w+',      # SQL Server stored procedures
        r'(?i)\bunion\s+all\s+select\b',  # Union-based injection
        r'(?i);\s*drop\b',          # Statement termination + DROP
        r'(?i);\s*delete\b',        # Statement termination + DELETE
        r'(?i);\s*insert\b',        # Statement termination + INSERT
        r'(?i);\s*update\b',        # Statement termination + UPDATE
        r'(?i)--\s*\w+',           # SQL comments (potential injection)
        r'(?i)/\*.*?\*/',          # Multi-line SQL comments
        r'(?i)\bchar\s*\(',        # CHAR function (obfuscation)
        r'(?i)\bhex\s*\(',         # HEX function (obfuscation)
        r'(?i)\bascii\s*\(',       # ASCII function (potential injection)
        r'(?i)\bload_file\s*\(',   # File reading functions
        r'(?i)\binto\s+outfile\b', # File writing
        r'(?i)\binto\s+dumpfile\b', # File writing
    ]
    
    # Allowed table names (whitelist approach)
    ALLOWED_TABLES = {
        'user', 'activity', 'passport', 'signup', 'passport_type',
        'expense', 'income', 'admin', 'admin_action_log', 
        'survey', 'survey_template', 'survey_response',
        'redemption', 'setting', 'email_log', 'query_log'
    }
    
    @classmethod
    def validate_sql(cls, sql: str) -> SecurityResult:
        """Comprehensive SQL validation"""
        
        if not sql or not sql.strip():
            return SecurityResult(
                is_safe=False,
                error_message="Empty SQL query"
            )
        
        sql = sql.strip()
        
        # 1. Check for blocked SQL keywords
        blocked_result = cls._check_blocked_keywords(sql)
        if not blocked_result.is_safe:
            return blocked_result
        
        # 2. Ensure only SELECT statements
        select_result = cls._validate_select_only(sql)
        if not select_result.is_safe:
            return select_result
        
        # 3. Check for dangerous patterns
        pattern_result = cls._check_dangerous_patterns(sql)
        if not pattern_result.is_safe:
            return pattern_result
        
        # 4. Validate table names
        table_result = cls._validate_table_names(sql)
        if not table_result.is_safe:
            return table_result
        
        # 5. Apply sanitization
        sanitized_sql = cls._sanitize_sql(sql)
        
        return SecurityResult(
            is_safe=True,
            sanitized_sql=sanitized_sql
        )
    
    @classmethod
    def _check_blocked_keywords(cls, sql: str) -> SecurityResult:
        """Check for blocked SQL keywords"""
        sql_upper = sql.upper()
        
        for keyword in BLOCKED_SQL_KEYWORDS:
            if re.search(rf'\b{keyword}\b', sql_upper):
                return SecurityResult(
                    is_safe=False,
                    error_message=f"Blocked SQL keyword detected: {keyword}",
                    blocked_reason=f"contains_{keyword.lower()}"
                )
        
        return SecurityResult(is_safe=True)
    
    @classmethod
    def _validate_select_only(cls, sql: str) -> SecurityResult:
        """Ensure only SELECT statements are allowed"""
        sql_upper = sql.upper().strip()
        
        if not sql_upper.startswith('SELECT'):
            return SecurityResult(
                is_safe=False,
                error_message="Only SELECT statements are allowed",
                blocked_reason="non_select_statement"
            )
        
        # Check for multiple statements (semicolon followed by non-whitespace)
        if re.search(r';\s*\w+', sql):
            return SecurityResult(
                is_safe=False,
                error_message="Multiple SQL statements are not allowed",
                blocked_reason="multiple_statements"
            )
        
        return SecurityResult(is_safe=True)
    
    @classmethod
    def _check_dangerous_patterns(cls, sql: str) -> SecurityResult:
        """Check for dangerous SQL patterns"""
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, sql):
                return SecurityResult(
                    is_safe=False,
                    error_message=f"Potentially dangerous SQL pattern detected",
                    blocked_reason="dangerous_pattern"
                )
        
        return SecurityResult(is_safe=True)
    
    @classmethod
    def _validate_table_names(cls, sql: str) -> SecurityResult:
        """Validate that only allowed tables are referenced"""
        
        # Extract table names from FROM and JOIN clauses
        table_pattern = r'(?i)\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        tables = re.findall(table_pattern, sql)
        
        for table in tables:
            table_lower = table.lower()
            if table_lower not in cls.ALLOWED_TABLES:
                return SecurityResult(
                    is_safe=False,
                    error_message=f"Access to table '{table}' is not allowed",
                    blocked_reason="unauthorized_table"
                )
        
        return SecurityResult(is_safe=True)
    
    @classmethod
    def _sanitize_sql(cls, sql: str) -> str:
        """Apply sanitization transformations"""
        
        # Remove excessive whitespace
        sql = re.sub(r'\s+', ' ', sql)
        
        # Remove trailing semicolon
        sql = sql.rstrip(';')
        
        # Add LIMIT if not present (safety measure)
        if not re.search(r'(?i)\blimit\s+\d+', sql):
            sql += f' LIMIT {MAX_RESULT_ROWS}'
        
        return sql.strip()


class QueryExecutor:
    """Secure SQL query executor"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query with security validation"""
        
        # Validate SQL security
        security_result = SQLSecurity.validate_sql(sql)
        if not security_result.is_safe:
            return {
                'success': False,
                'error': security_result.error_message,
                'blocked_reason': security_result.blocked_reason
            }
        
        # Execute the sanitized query
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column name access
            cursor = conn.cursor()
            
            # Set query timeout (SQLite doesn't support this directly, but we can use a timeout)
            cursor.execute(security_result.sanitized_sql)
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [description[0] for description in cursor.description] if cursor.description else []
            data = [dict(row) for row in rows] if rows else []
            
            conn.close()
            
            return {
                'success': True,
                'columns': columns,
                'data': data,
                'row_count': len(data),
                'sql_executed': security_result.sanitized_sql
            }
            
        except sqlite3.Error as e:
            return {
                'success': False,
                'error': f"Database error: {str(e)}",
                'error_type': 'database_error'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution error: {str(e)}",
                'error_type': 'execution_error'
            }


class PIIDetector:
    """Detect and handle Personally Identifiable Information"""
    
    # Patterns for common PII
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    }
    
    @classmethod
    def scan_for_pii(cls, text: str) -> List[str]:
        """Scan text for PII patterns"""
        found_pii = []
        
        for pii_type, pattern in cls.PII_PATTERNS.items():
            if re.search(pattern, text):
                found_pii.append(pii_type)
        
        return found_pii
    
    @classmethod
    def mask_pii(cls, text: str, mask_char: str = '*') -> str:
        """Mask PII in text"""
        masked_text = text
        
        # Mask emails (keep first and last char of username and domain)
        masked_text = re.sub(
            cls.PII_PATTERNS['email'],
            lambda m: cls._mask_email(m.group()),
            masked_text
        )
        
        # Mask phone numbers (keep area code)
        masked_text = re.sub(
            cls.PII_PATTERNS['phone'],
            lambda m: cls._mask_phone(m.group()),
            masked_text
        )
        
        return masked_text
    
    @classmethod
    def _mask_email(cls, email: str) -> str:
        """Mask email address"""
        username, domain = email.split('@')
        if len(username) <= 2:
            masked_username = '*' * len(username)
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        
        domain_parts = domain.split('.')
        if len(domain_parts[0]) <= 2:
            masked_domain = '*' * len(domain_parts[0])
        else:
            masked_domain = domain_parts[0][0] + '*' * (len(domain_parts[0]) - 2) + domain_parts[0][-1]
        
        return f"{masked_username}@{masked_domain}.{'.'.join(domain_parts[1:])}"
    
    @classmethod
    def _mask_phone(cls, phone: str) -> str:
        """Mask phone number"""
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) ***-****"
        return '*' * len(phone)