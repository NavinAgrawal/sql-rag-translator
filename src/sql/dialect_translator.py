#!/usr/bin/env python3
"""
SQL Dialect Translator
Converts PostgreSQL queries to other database dialects

Author: Navin B Agrawal
Date: June 2025
"""

import re
from typing import Dict, List, Tuple


class SQLDialectTranslator:
    """Translates SQL queries between different database dialects"""
    
    def __init__(self):
        self.dialect_info = {
            'postgresql': {
                'name': 'PostgreSQL',
                'description': 'Advanced open-source database with JSON support',
                'features': ['JSON', 'Arrays', 'Window Functions', 'CTEs', 'UPSERT']
            },
            'mysql': {
                'name': 'MySQL',
                'description': 'Popular open-source database for web applications',
                'features': ['JSON (5.7+)', 'Full-Text Search', 'Partitioning', 'Replication']
            },
            'oracle': {
                'name': 'Oracle Database',
                'description': 'Enterprise database with advanced analytics',
                'features': ['Advanced Analytics', 'Partitioning', 'Data Guard', 'RAC']
            },
            'sqlserver': {
                'name': 'SQL Server',
                'description': 'Microsoft enterprise database platform',
                'features': ['T-SQL', 'Integration Services', 'Analysis Services', 'Reporting']
            }
        }
    
    def get_available_dialects(self) -> List[str]:
        """Get list of supported dialects"""
        return list(self.dialect_info.keys())
    
    def get_dialect_info(self, dialect: str) -> Dict:
        """Get information about a specific dialect"""
        return self.dialect_info.get(dialect.lower(), {})
    
    def translate_query(self, sql_query: str, target_dialect: str) -> Dict:
        """Translate SQL query to target dialect"""
        target_dialect = target_dialect.lower()
        
        if target_dialect not in self.dialect_info:
            return {
                'success': False,
                'error': f"Unsupported dialect: {target_dialect}",
                'supported_dialects': list(self.dialect_info.keys())
            }
        
        try:
            if target_dialect == 'postgresql':
                # Already PostgreSQL, return as-is
                translated_sql = sql_query
                notes = ["Query is already in PostgreSQL format"]
            elif target_dialect == 'mysql':
                translated_sql, notes = self._translate_to_mysql(sql_query)
            elif target_dialect == 'oracle':
                translated_sql, notes = self._translate_to_oracle(sql_query)
            elif target_dialect == 'sqlserver':
                translated_sql, notes = self._translate_to_sqlserver(sql_query)
            else:
                return {
                    'success': False,
                    'error': f"Translation to {target_dialect} not implemented yet"
                }
            
            return {
                'success': True,
                'original_sql': sql_query,
                'translated_sql': translated_sql,
                'target_dialect': target_dialect,
                'dialect_name': self.dialect_info[target_dialect]['name'],
                'translation_notes': notes,
                'compatibility_notes': self._get_compatibility_notes(target_dialect)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Translation error: {str(e)}"
            }
    
    def _translate_to_mysql(self, sql: str) -> Tuple[str, List[str]]:
        """Translate PostgreSQL to MySQL"""
        translated = sql
        notes = []
        
        # Replace PostgreSQL-specific functions
        replacements = [
            # Date functions
            (r'CURRENT_DATE', 'CURDATE()', 'Current date function'),
            (r'CURRENT_TIMESTAMP', 'NOW()', 'Current timestamp function'),
            (r'DATE_TRUNC\s*\(\s*[\'"]month[\'"]\s*,\s*([^)]+)\)', 
             r'DATE_FORMAT(\1, "%Y-%m-01")', 'Date truncation to month'),
            
            # String functions
            (r'STRING_AGG\s*\(\s*([^,]+)\s*,\s*([^)]+)\)', 
             r'GROUP_CONCAT(\1 SEPARATOR \2)', 'String aggregation'),
            
            # Limit syntax (already compatible)
            # Boolean literals
            (r'\bTRUE\b', '1', 'Boolean TRUE'),
            (r'\bFALSE\b', '0', 'Boolean FALSE'),
            
            # Data types
            (r'\bSERIAL\b', 'INT AUTO_INCREMENT', 'Auto-increment integer'),
            (r'\bBIGSERIAL\b', 'BIGINT AUTO_INCREMENT', 'Auto-increment big integer'),
            (r'\bTEXT\b', 'LONGTEXT', 'Large text field'),
        ]
        
        for pattern, replacement, note in replacements:
            if re.search(pattern, translated, re.IGNORECASE):
                translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
                notes.append(f"Converted {note}")
        
        # Handle INTERVAL (more complex)
        interval_pattern = r"INTERVAL\s+'(\d+)\s+(\w+)'"
        def interval_replacement(match):
            value, unit = match.groups()
            return f"INTERVAL {value} {unit.upper()}"
        
        if re.search(interval_pattern, translated, re.IGNORECASE):
            translated = re.sub(interval_pattern, interval_replacement, translated, flags=re.IGNORECASE)
            notes.append("Converted INTERVAL syntax")
        
        return translated, notes
    
    def _translate_to_oracle(self, sql: str) -> Tuple[str, List[str]]:
        """Translate PostgreSQL to Oracle"""
        translated = sql
        notes = []
        
        # Replace PostgreSQL-specific functions
        replacements = [
            # Date functions
            (r'CURRENT_DATE', 'SYSDATE', 'Current date function'),
            (r'CURRENT_TIMESTAMP', 'SYSTIMESTAMP', 'Current timestamp function'),
            (r'DATE_TRUNC\s*\(\s*[\'"]month[\'"]\s*,\s*([^)]+)\)', 
             r'TRUNC(\1, "MM")', 'Date truncation to month'),
            
            # String functions
            (r'STRING_AGG\s*\(\s*([^,]+)\s*,\s*([^)]+)\)', 
             r'LISTAGG(\1, \2) WITHIN GROUP (ORDER BY \1)', 'String aggregation'),
            
            # Boolean literals
            (r'\bTRUE\b', '1', 'Boolean TRUE'),
            (r'\bFALSE\b', '0', 'Boolean FALSE'),
        ]
        
        for pattern, replacement, note in replacements:
            if re.search(pattern, translated, re.IGNORECASE):
                translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
                notes.append(f"Converted {note}")
        
        # Handle LIMIT with ORDER BY (Oracle needs subquery)
        limit_pattern = r'(.*ORDER BY\s+[^;]+)\s+LIMIT\s+(\d+)'
        if re.search(limit_pattern, translated, re.IGNORECASE | re.DOTALL):
            def limit_replacement(match):
                query_part, limit_num = match.groups()
                return f"SELECT * FROM ({query_part}) WHERE ROWNUM <= {limit_num}"
            
            translated = re.sub(limit_pattern, limit_replacement, translated, flags=re.IGNORECASE | re.DOTALL)
            notes.append("Converted LIMIT with subquery for Oracle")
        
        return translated, notes
    
    def _translate_to_sqlserver(self, sql: str) -> Tuple[str, List[str]]:
        """Translate PostgreSQL to SQL Server"""
        translated = sql
        notes = []
        
        # Replace PostgreSQL-specific functions
        replacements = [
            # Date functions
            (r'CURRENT_DATE', 'GETDATE()', 'Current date function'),
            (r'CURRENT_TIMESTAMP', 'GETDATE()', 'Current timestamp function'),
            (r'DATE_TRUNC\s*\(\s*[\'"]month[\'"]\s*,\s*([^)]+)\)', 
             r'DATEFROMPARTS(YEAR(\1), MONTH(\1), 1)', 'Date truncation to month'),
            
            # String functions
            (r'STRING_AGG\s*\(\s*([^,]+)\s*,\s*([^)]+)\)', 
             r'STRING_AGG(\1, \2)', 'String aggregation (SQL Server 2017+)'),
            
            # Boolean literals
            (r'\bTRUE\b', '1', 'Boolean TRUE'),
            (r'\bFALSE\b', '0', 'Boolean FALSE'),
            
            # Data types
            (r'\bSERIAL\b', 'INT IDENTITY(1,1)', 'Auto-increment integer'),
            (r'\bBIGSERIAL\b', 'BIGINT IDENTITY(1,1)', 'Auto-increment big integer'),
            (r'\bTEXT\b', 'NVARCHAR(MAX)', 'Large text field'),
        ]
        
        for pattern, replacement, note in replacements:
            if re.search(pattern, translated, re.IGNORECASE):
                translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
                notes.append(f"Converted {note}")
        
        # Handle LIMIT -> TOP conversion (move to SELECT clause)
        limit_pattern = r'(SELECT\s+)(.*?)(.*ORDER BY\s+[^;]+)\s+LIMIT\s+(\d+)'
        if re.search(limit_pattern, translated, re.IGNORECASE | re.DOTALL):
            def limit_replacement(match):
                select_word, select_clause, order_clause, limit_num = match.groups()
                return f'{select_word}TOP {limit_num} {select_clause}{order_clause}'
            
            translated = re.sub(limit_pattern, limit_replacement, translated, flags=re.IGNORECASE | re.DOTALL)
            notes.append("Converted LIMIT to TOP clause")
        
        return translated, notes
    
    def _get_compatibility_notes(self, dialect: str) -> List[str]:
        """Get general compatibility notes for the dialect"""
        compatibility_notes = {
            'mysql': [
                "MySQL 5.7+ required for JSON functions",
                "String aggregation requires GROUP_CONCAT",
                "Case-sensitive table names on Linux/Unix systems",
                "Limited window function support in older versions"
            ],
            'oracle': [
                "ROWNUM-based limiting may affect performance with large result sets",
                "Date format differences may require adjustment",
                "LISTAGG has length limitations (4000 chars)",
                "Consider using FETCH FIRST for Oracle 12c+"
            ],
            'sqlserver': [
                "STRING_AGG available in SQL Server 2017+",
                "Use OFFSET/FETCH for better pagination in SQL Server 2012+",
                "NVARCHAR recommended for Unicode text",
                "Consider using APPLY for complex joins"
            ],
            'postgresql': [
                "This is the source dialect - no compatibility issues"
            ]
        }
        
        return compatibility_notes.get(dialect, [])
    
    def batch_translate(self, sql_query: str) -> Dict:
        """Translate query to all supported dialects"""
        results = {}
        
        for dialect in self.get_available_dialects():
            if dialect != 'postgresql':  # Skip source dialect
                results[dialect] = self.translate_query(sql_query, dialect)
        
        return {
            'original_sql': sql_query,
            'translations': results,
            'supported_dialects': self.get_available_dialects()
        }


def main():
    """Test the dialect translator"""
    translator = SQLDialectTranslator()
    
    test_query = """
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        STRING_AGG(p.product_name, ', ') as products,
        COUNT(a.account_id) as account_count
    FROM customers c
    LEFT JOIN accounts a ON c.customer_id = a.customer_id
    LEFT JOIN products p ON a.product_id = p.product_id
    WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY c.customer_id, c.first_name, c.last_name
    ORDER BY account_count DESC
    LIMIT 10;
    """
    
    print("🔄 Testing SQL Dialect Translator")
    print("=" * 50)
    
    # Test translation to each dialect
    for dialect in ['mysql', 'oracle', 'sqlserver']:
        print(f"\n📝 Translating to {dialect.upper()}:")
        result = translator.translate_query(test_query, dialect)
        
        if result['success']:
            print(f"✅ Success - {result['dialect_name']}")
            print(f"Notes: {', '.join(result['translation_notes'])}")
        else:
            print(f"❌ Failed: {result['error']}")


if __name__ == "__main__":
    main()