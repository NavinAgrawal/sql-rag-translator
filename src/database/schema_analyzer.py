#!/usr/bin/env python3
"""
Database Schema Analyzer for SQL RAG System
Extracts and analyzes database schema for embedding generation
"""

import psycopg2
import json
from typing import Dict, List, Any

class SchemaAnalyzer:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = db_connection.cursor()

    def extract_complete_schema(self) -> Dict[str, Any]:
        """Extract complete schema information for RAG processing"""
        
        schema_info = {
            'tables': {},
            'relationships': [],
            'indexes': [],
            'constraints': [],
            'sample_data': {}
        }
        
        # Get all tables
        self.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = self.cursor.fetchall()
        
        for table_row in tables:
            table_name = table_row[0]
            schema_info['tables'][table_name] = {
                'columns': self.get_table_columns(table_name),
                'comment': None,
                'sample_queries': self.generate_sample_queries(table_name),
                'row_count': self.get_row_count(table_name)
            }
        
        # Get foreign key relationships
        schema_info['relationships'] = self.get_foreign_keys()
        
        # Get indexes
        schema_info['indexes'] = self.get_indexes()
        
        return schema_info
    
    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Get detailed column information for a table"""
        self.cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                col_description(pgc.oid, a.attnum) as column_comment
            FROM information_schema.columns c
            LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
            LEFT JOIN pg_attribute a ON a.attrelid = pgc.oid AND a.attname = c.column_name
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3],
                'max_length': row[4],
                'precision': row[5],
                'scale': row[6],
                'comment': row[7]
            })
        
        return columns
    
    def get_foreign_keys(self) -> List[Dict]:
        """Get all foreign key relationships"""
        self.cursor.execute("""
            SELECT 
                tc.table_name as source_table,
                kcu.column_name as source_column,
                ccu.table_name as target_table,
                ccu.column_name as target_column,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        relationships = []
        for row in self.cursor.fetchall():
            relationships.append({
                'source_table': row[0],
                'source_column': row[1],
                'target_table': row[2],
                'target_column': row[3],
                'constraint_name': row[4]
            })
        
        return relationships
    
    def get_indexes(self) -> List[Dict]:
        """Get index information"""
        self.cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        
        indexes = []
        for row in self.cursor.fetchall():
            indexes.append({
                'schema': row[0],
                'table': row[1],
                'name': row[2],
                'definition': row[3]
            })
        
        return indexes
    
    def get_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table"""
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return self.cursor.fetchone()[0]
    
    def generate_sample_queries(self, table_name: str) -> List[str]:
        """Generate sample queries for a table"""
        
        # Get primary key
        self.cursor.execute("""
            SELECT column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = %s 
            AND tc.constraint_type = 'PRIMARY KEY';
        """, (table_name,))
        
        pk_columns = [row[0] for row in self.cursor.fetchall()]
        pk_col = pk_columns[0] if pk_columns else 'id'
        
        samples = [
            f"SELECT * FROM {table_name} LIMIT 10;",
            f"SELECT COUNT(*) FROM {table_name};",
            f"SELECT * FROM {table_name} ORDER BY {pk_col} DESC LIMIT 5;"
        ]
        
        # Add date-based queries if date columns exist
        date_columns = self.get_date_columns(table_name)
        if date_columns:
            date_col = date_columns[0]
            samples.extend([
                f"SELECT * FROM {table_name} WHERE {date_col} >= CURRENT_DATE - INTERVAL '30 days';",
                f"SELECT DATE({date_col}), COUNT(*) FROM {table_name} GROUP BY DATE({date_col}) ORDER BY DATE({date_col}) DESC LIMIT 10;"
            ])
        
        return samples
    
    def get_date_columns(self, table_name: str) -> List[str]:
        """Get date/timestamp columns for a table"""
        self.cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s 
            AND data_type IN ('date', 'timestamp', 'timestamp with time zone', 'timestamp without time zone')
            ORDER BY ordinal_position;
        """, (table_name,))
        
        return [row[0] for row in self.cursor.fetchall()]
    
    def create_schema_embeddings_text(self) -> str:
        """Create text representation of schema for embedding"""
        schema = self.extract_complete_schema()
        
        text_parts = []
        text_parts.append("BANKING DATABASE SCHEMA DOCUMENTATION")
        text_parts.append("=" * 50)
        
        # Add table descriptions
        for table_name, table_info in schema['tables'].items():
            text_parts.append(f"\nTABLE: {table_name}")
            text_parts.append(f"Description: {self.get_table_description(table_name)}")
            text_parts.append(f"Row Count: {table_info['row_count']:,}")
            
            text_parts.append("Columns:")
            for col in table_info['columns']:
                col_desc = f"  - {col['name']} ({col['type']})"
                if not col['nullable']:
                    col_desc += " NOT NULL"
                if col['comment']:
                    col_desc += f" - {col['comment']}"
                text_parts.append(col_desc)
            
            text_parts.append("Sample Queries:")
            for query in table_info['sample_queries']:
                text_parts.append(f"  - {query}")
        
        # Add relationships
        text_parts.append("\nTABLE RELATIONSHIPS:")
        for rel in schema['relationships']:
            text_parts.append(f"  {rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']}")
        
        return "\n".join(text_parts)
    
    def get_table_description(self, table_name: str) -> str:
        """Get human-readable description of table purpose"""
        descriptions = {
            'countries': 'Reference table containing country information with currencies and tax rates',
            'states': 'Geographic reference for US states and provinces',
            'cities': 'City information with population and economic data',
            'regions': 'Bank operational regions for branch organization',
            'branches': 'Physical bank branch locations and details',
            'departments': 'Bank organizational departments',
            'employees': 'Bank staff information with hierarchy and compensation',
            'customer_segments': 'Customer classification tiers based on relationship value',
            'customer_types': 'Categories of customers (individual, business, corporate)',
            'customers': 'Customer profiles with demographics and financial information',
            'product_categories': 'Banking product classification (deposits, loans, cards)',
            'products': 'Specific banking products with terms and fees',
            'accounts': 'Customer accounts with balances and transaction limits',
            'transaction_types': 'Classification of banking transaction types',
            'merchant_categories': 'Merchant category codes for transaction classification',
            'merchants': 'Business entities where transactions occur',
            'transactions': 'Individual banking transactions with amounts and details'
        }
        
        return descriptions.get(table_name, f'Database table: {table_name}')

def main():
    """Test the schema analyzer"""
    conn = psycopg2.connect(host='localhost', database='banking_rag_db', user='nba')
    
    analyzer = SchemaAnalyzer(conn)
    
    print("🔍 Analyzing database schema...")
    schema_text = analyzer.create_schema_embeddings_text()
    
    # Save to file
    with open('data/schemas/schema_analysis.txt', 'w') as f:
        f.write(schema_text)
    
    # Save JSON version
    schema_json = analyzer.extract_complete_schema()
    with open('data/schemas/schema_analysis.json', 'w') as f:
        json.dump(schema_json, f, indent=2, default=str)
    
    print(f"✅ Schema analysis complete!")
    print(f"📄 Text version: data/schemas/schema_analysis.txt")
    print(f"📋 JSON version: data/schemas/schema_analysis.json")
    
    # Show sample
    print(f"\n📝 Sample schema text (first 500 chars):")
    print(schema_text[:500] + "...")
    
    conn.close()

if __name__ == "__main__":
    main()
