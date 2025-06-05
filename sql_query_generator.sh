 #!/bin/bash

cat > src/sql/query_generator.py << 'EOF'
#!/usr/bin/env python3
"""
Natural Language to SQL Query Generator
Converts user questions into database queries using schema context
"""

import json
import os
from typing import Dict, List, Any, Optional
from anthropic import Anthropic

class NLToSQLGenerator:
    def __init__(self, schema_file_path: str, anthropic_api_key: str):
        """Initialize with schema information and LLM client"""
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.schema = self.load_schema(schema_file_path)
        self.table_descriptions = self.load_table_descriptions()
    
    def load_schema(self, schema_file_path: str) -> Dict[str, Any]:
        """Load schema information from JSON file"""
        with open(schema_file_path, 'r') as f:
            return json.load(f)
    
    def load_table_descriptions(self) -> Dict[str, str]:
        """Load human-readable table descriptions"""
        return {
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
    
    def identify_relevant_tables(self, user_question: str) -> List[str]:
        """Identify which tables are most relevant to the user's question"""
        question_lower = user_question.lower()
        relevant_tables = []
        
        # Banking domain keywords mapping to tables
        keyword_mappings = {
            'customer': ['customers', 'customer_types', 'customer_segments'],
            'account': ['accounts', 'products', 'product_categories'],
            'transaction': ['transactions', 'transaction_types', 'merchants'],
            'employee': ['employees', 'departments'],
            'branch': ['branches', 'regions'],
            'balance': ['accounts'],
            'deposit': ['transactions', 'accounts'],
            'withdrawal': ['transactions', 'accounts'],
            'transfer': ['transactions'],
            'loan': ['products', 'accounts'],
            'credit': ['products', 'accounts', 'customers'],
            'city': ['cities', 'branches', 'customers'],
            'state': ['states', 'cities'],
            'region': ['regions', 'branches'],
            'merchant': ['merchants', 'merchant_categories', 'transactions'],
            'salary': ['employees'],
            'manager': ['employees'],
            'segment': ['customer_segments', 'customers']
        }
        
        for keyword, tables in keyword_mappings.items():
            if keyword in question_lower:
                relevant_tables.extend(tables)
        
        # Remove duplicates and ensure we have at least some tables
        relevant_tables = list(set(relevant_tables))
        
        if not relevant_tables:
            # Default to core banking tables
            relevant_tables = ['customers', 'accounts', 'transactions']
        
        return relevant_tables[:6]  # Limit to 6 most relevant tables
    
    def build_schema_context(self, relevant_tables: List[str]) -> str:
        """Build schema context for the LLM prompt"""
        context_parts = []
        context_parts.append("RELEVANT DATABASE SCHEMA:")
        context_parts.append("=" * 40)
        
        for table_name in relevant_tables:
            if table_name in self.schema['tables']:
                table_info = self.schema['tables'][table_name]
                context_parts.append(f"\nTABLE: {table_name}")
                context_parts.append(f"Purpose: {self.table_descriptions.get(table_name, 'Banking table')}")
                context_parts.append(f"Rows: {table_info['row_count']:,}")
                
                context_parts.append("Columns:")
                for col in table_info['columns']:
                    col_desc = f"  - {col['name']}: {col['type']}"
                    if not col['nullable']:
                        col_desc += " (required)"
                    context_parts.append(col_desc)
        
        # Add relationships
        context_parts.append(f"\nTABLE RELATIONSHIPS:")
        for rel in self.schema['relationships']:
            if rel['source_table'] in relevant_tables or rel['target_table'] in relevant_tables:
                context_parts.append(f"  {rel['source_table']}.{rel['source_column']} → {rel['target_table']}.{rel['target_column']}")
        
        return "\n".join(context_parts)
    
    def generate_sql_query(self, user_question: str, target_dialect: str = 'postgresql') -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        
        # Identify relevant tables
        relevant_tables = self.identify_relevant_tables(user_question)
        
        # Build schema context
        schema_context = self.build_schema_context(relevant_tables)
        
        # Create the prompt
        prompt = self.create_sql_prompt(user_question, schema_context, target_dialect)
        
        # Generate SQL using Claude
        try:
            response = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            sql_response = response.content[0].text
            
            # Parse the response to extract SQL and explanation
            parsed_response = self.parse_sql_response(sql_response)
            
            return {
                'success': True,
                'sql_query': parsed_response['sql'],
                'explanation': parsed_response['explanation'],
                'relevant_tables': relevant_tables,
                'dialect': target_dialect,
                'confidence': parsed_response.get('confidence', 'medium')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'relevant_tables': relevant_tables,
                'dialect': target_dialect
            }
    
    def create_sql_prompt(self, user_question: str, schema_context: str, target_dialect: str) -> str:
        """Create the prompt for SQL generation"""
        
        prompt_template = f"""You are an expert SQL developer specializing in banking database queries. Your task is to convert natural language questions into accurate {target_dialect.upper()} SQL queries.

{schema_context}

IMPORTANT GUIDELINES:
1. Generate syntactically correct {target_dialect.upper()} queries
2. Use proper JOINs to connect related tables
3. Include appropriate WHERE clauses for filtering
4. Use aggregate functions (COUNT, SUM, AVG) when asking for totals or averages
5. Add ORDER BY for meaningful sorting
6. Use LIMIT for top/bottom queries
7. Handle NULL values appropriately
8. Include table aliases for readability
9. Use proper date formatting for PostgreSQL
10. Follow banking industry best practices

RESPONSE FORMAT:
Provide your response in this exact format:

[Your SQL query here]

EXPLANATION:
[Brief explanation of what the query does and why you chose this approach]

CONFIDENCE: [high/medium/low]

USER QUESTION: {user_question}

Generate the SQL query now:"""

        return prompt_template
    
    def parse_sql_response(self, response_text: str) -> Dict[str, str]:
        """Parse the LLM response to extract SQL query and explanation"""
        
        # Extract SQL query (between ```sql and ```)
        sql_start = response_text.find('```sql')
        sql_end = response_text.find('```', sql_start + 6)
        
        if sql_start != -1 and sql_end != -1:
            sql_query = response_text[sql_start + 6:sql_end].strip()
        else:
            # Fallback: look for any code block
            sql_start = response_text.find('```')
            sql_end = response_text.find('```', sql_start + 3)
            if sql_start != -1 and sql_end != -1:
                sql_query = response_text[sql_start + 3:sql_end].strip()
            else:
                sql_query = "-- Could not extract SQL query from response"
        
        # Extract explanation
        explanation_start = response_text.find('EXPLANATION:')
        confidence_start = response_text.find('CONFIDENCE:')
        
        if explanation_start != -1:
            if confidence_start != -1:
                explanation = response_text[explanation_start + 12:confidence_start].strip()
            else:
                explanation = response_text[explanation_start + 12:].strip()
        else:
            explanation = "No explanation provided"
        
        # Extract confidence
        confidence = 'medium'  # default
        if confidence_start != -1:
            confidence_text = response_text[confidence_start + 11:].strip().lower()
            if any(level in confidence_text for level in ['high', 'medium', 'low']):
                for level in ['high', 'medium', 'low']:
                    if level in confidence_text:
                        confidence = level
                        break
        
        return {
            'sql': sql_query,
            'explanation': explanation,
            'confidence': confidence
        }

def main():
    """Test the query generator"""
    
    # Check for Anthropic API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Initialize generator
    generator = NLToSQLGenerator(
        schema_file_path='data/schemas/schema_analysis.json',
        anthropic_api_key=api_key
    )
    
    # Test queries
    test_questions = [
        "Show me the top 5 customers by account balance",
        "How many transactions happened last month?",
        "Which branch has the most employees?",
        "List all customers from California with their total account balances",
        "Show me employees who earn more than $100,000"
    ]
    
    print("🤖 Testing Natural Language to SQL Generator")
    print("=" * 60)
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        print("-" * 40)
        
        result = generator.generate_sql_query(question, 'postgresql')
        
        if result['success']:
            print(f"✅ Generated SQL:")
            print(result['sql_query'])
            print(f"\n📝 Explanation: {result['explanation']}")
            print(f"🎯 Confidence: {result['confidence']}")
            print(f"📊 Tables used: {', '.join(result['relevant_tables'])}")
        else:
            print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()
EOF