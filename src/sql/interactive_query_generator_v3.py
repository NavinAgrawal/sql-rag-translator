#!/usr/bin/env python3
"""
Multi-Dialect Interactive SQL RAG Query Generator
Enhanced CLI with support for multiple database dialects

Author: Navin B Agrawal
Date: June 2025
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from database.schema_analyzer import SchemaAnalyzer
    from sql.query_generator import NLToSQLGenerator
    from sql.dialect_translator import SQLDialectTranslator
    import psycopg2
    from psycopg2 import sql
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root and have installed dependencies")
    sys.exit(1)


class MultiDialectInteractiveSQLGenerator:
    """Multi-dialect Interactive CLI for SQL query generation"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'banking_rag_db',
            'user': os.getenv('USER'),
            'password': ''
        }
        self.connection = None
        self.schema_analyzer = None
        self.query_generator = None
        self.dialect_translator = SQLDialectTranslator()
        self.session_queries = []
        self.enhanced_schema_info = None
        self.current_dialect = 'postgresql'  # Default dialect
        
        print(f"🔧 Database config: user='{self.db_config['user']}', database='{self.db_config['database']}'")
        
    def connect_database(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            print(f"✅ Connected to database: {self.db_config['database']}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("Make sure PostgreSQL is running and the database exists")
            return False
    
    def enhance_schema_context(self, schema_info):
        """Enhance schema with better relationship documentation"""
        enhanced_schema = schema_info.copy()
        
        # Add explicit relationship paths for common business queries
        enhanced_schema['relationship_paths'] = {
            'customer_to_transactions': [
                'customers.customer_id → accounts.customer_id',
                'accounts.account_id → transactions.account_id'
            ],
            'customer_to_balances': [
                'customers.customer_id → accounts.customer_id',
                'Use accounts.current_balance for current balances'
            ],
            'geographic_customer_queries': [
                'customers.city_id → cities.city_id',
                'cities.state_id → states.state_id',
                'For state filtering: JOIN states ON cities.state_id = states.state_id'
            ],
            'branch_employee_queries': [
                'branches.branch_id → employees.branch_id',
                'Filter active employees: WHERE employees.termination_date IS NULL'
            ]
        }
        
        # Add common query patterns
        enhanced_schema['query_patterns'] = {
            'customer_balances': {
                'description': 'For customer balance queries, use accounts.current_balance',
                'tables': ['customers', 'accounts'],
                'join': 'customers.customer_id = accounts.customer_id',
                'aggregate': 'SUM(accounts.current_balance) as total_balance'
            },
            'customer_transactions': {
                'description': 'For customer transaction queries, go through accounts',
                'tables': ['customers', 'accounts', 'transactions'],
                'joins': [
                    'customers.customer_id = accounts.customer_id',
                    'accounts.account_id = transactions.account_id'
                ],
                'note': 'transactions table has NO customer_id column - must go through accounts'
            },
            'geographic_customers': {
                'description': 'For geographic customer queries',
                'tables': ['customers', 'cities', 'states'],
                'joins': [
                    'customers.city_id = cities.city_id',
                    'cities.state_id = states.state_id'
                ]
            }
        }
        
        return enhanced_schema
    
    def initialize_components(self):
        """Initialize all components"""
        try:
            # Initialize schema analyzer
            self.schema_analyzer = SchemaAnalyzer(self.connection)
            schema_info = self.schema_analyzer.extract_complete_schema()
            
            # Enhance schema context
            self.enhanced_schema_info = self.enhance_schema_context(schema_info)
            
            # Save enhanced schema
            schema_file = "data/schemas/enhanced_schema_analysis.json"
            os.makedirs("data/schemas", exist_ok=True)
            
            with open(schema_file, 'w') as f:
                json.dump(self.enhanced_schema_info, f, indent=2)
            
            # Get API key
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("❌ ANTHROPIC_API_KEY not found in environment")
                return False
            
            # Initialize query generator
            self.query_generator = NLToSQLGenerator(schema_file, api_key)
            
            print(f"📊 Schema loaded: {len(schema_info['tables'])} tables with enhanced relationships")
            print(f"🔄 Dialect translator initialized with {len(self.dialect_translator.get_available_dialects())} dialects")
            return True
        except Exception as e:
            print(f"❌ Component initialization failed: {e}")
            return False
    
    def display_welcome(self):
        """Display welcome screen with dialect info"""
        print("\n" + "="*70)
        print("🏦 SQL RAG Translator - Multi-Dialect Interactive Mode")
        print("="*70)
        print(f"📅 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Database: {self.db_config['database']} (PostgreSQL)")
        print(f"🎯 Current dialect: {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}")
        print(f"🌐 Available dialects: {', '.join(self.dialect_translator.get_available_dialects())}")
        print("💡 Type 'help' for examples, 'dialects' to switch, 'quit' to exit")
        print("-"*70)
    
    def display_dialect_menu(self):
        """Display dialect selection menu"""
        print("\n🌐 Available Database Dialects:")
        print("=" * 45)
        
        dialects = self.dialect_translator.get_available_dialects()
        for i, dialect in enumerate(dialects, 1):
            info = self.dialect_translator.get_dialect_info(dialect)
            current_marker = " (current)" if dialect == self.current_dialect else ""
            print(f"{i}. {info['name']}{current_marker}")
            print(f"   {info['description']}")
            if i < len(dialects):
                print()
        
        print("\n💡 Note: Queries are generated in PostgreSQL, then translated to other dialects")
        print("-" * 45)
        
        try:
            choice = input(f"\nSelect dialect [1-{len(dialects)}] or press Enter to keep current: ").strip()
            if choice:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(dialects):
                    old_dialect = self.current_dialect
                    self.current_dialect = dialects[choice_idx]
                    dialect_info = self.dialect_translator.get_dialect_info(self.current_dialect)
                    print(f"✅ Switched from {old_dialect} to {dialect_info['name']}")
                else:
                    print("❌ Invalid choice")
            else:
                print(f"Keeping current dialect: {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}")
        except ValueError:
            print("❌ Invalid input")
    
    def display_help(self):
        """Display enhanced help"""
        print("\n📚 Example Queries:")
        print("=" * 50)
        
        examples = [
            ("Customer Analysis", [
                "Show me the top 5 customers by account balance",
                "List all customers from California with their total balances",
                "Find customers with more than $500,000 in total balances"
            ]),
            ("Branch & Employee Queries", [
                "Which branch has the most employees?",
                "Show me employees who earn more than $100,000",
                "List all branches in Texas"
            ]),
            ("Product & Account Queries", [
                "What are the different account types available?",
                "Show me all checking account products",
                "Which products are most popular?"
            ]),
            ("Transaction Analysis", [
                "How many transactions were processed last month?",
                "Show me the largest transactions this year",
                "What are the most common transaction types?"
            ])
        ]
        
        for category, queries in examples:
            print(f"\n🎯 {category}:")
            for i, query in enumerate(queries, 1):
                print(f"   {i}. {query}")
        
        print(f"\n🎮 Commands:")
        print("- 'help' - Show this help")
        print("- 'dialects' - Switch database dialect")
        print("- 'translate <query>' - Translate to all dialects")
        print("- 'history' - Show query history")
        print("- 'schema' - Show table relationships")
        print("- 'quit' or 'exit' - Exit the application")
        print("-" * 50)
    
    def display_schema_info(self):
        """Display schema relationships"""
        print("\n📋 Key Table Relationships:")
        print("=" * 40)
        
        relationships = [
            "👥 Customers → Accounts → Transactions",
            "🏢 Regions → Branches → Employees",
            "🌍 Countries → States → Cities → Customers",
            "💳 Product Categories → Products → Accounts",
            "🏪 Merchant Categories → Merchants → Transactions"
        ]
        
        for rel in relationships:
            print(f"  {rel}")
        
        print(f"\n💡 Key Notes:")
        print("  • Transactions connect to customers through accounts")
        print("  • Use accounts.current_balance for customer balances")
        print("  • Filter active employees with termination_date IS NULL")
        print("-" * 40)
    
    def translate_to_all_dialects(self, sql_query):
        """Translate query to all dialects and display"""
        print(f"\n🔄 Translating to all database dialects...")
        print("=" * 60)
        
        batch_result = self.dialect_translator.batch_translate(sql_query)
        
        for dialect, result in batch_result['translations'].items():
            dialect_info = self.dialect_translator.get_dialect_info(dialect)
            print(f"\n📝 {dialect_info['name']} ({dialect.upper()}):")
            print("-" * 40)
            
            if result['success']:
                print(result['translated_sql'])
                if result['translation_notes']:
                    print(f"\n💡 Changes: {', '.join(result['translation_notes'])}")
            else:
                print(f"❌ Translation failed: {result['error']}")
        
        print("=" * 60)
    
    def process_question(self, question):
        """Process question with multi-dialect support"""
        print(f"\n🤖 Generating SQL query...")
        
        try:
            # Generate SQL using query generator
            result = self.query_generator.generate_sql_query(question, 'postgresql')
            
            if result['success']:
                sql_query = result['sql_query']
                confidence = result.get('confidence_score', result.get('confidence', 'Not available'))
                
                if isinstance(confidence, (int, float)):
                    confidence_display = f"{confidence:.1%}"
                else:
                    confidence_display = str(confidence)
                
                print(f"✅ Query generated successfully! (Confidence: {confidence_display})")
                
                # Show original PostgreSQL query
                print(f"\n📝 Generated SQL (PostgreSQL):")
                print("=" * 50)
                print(sql_query)
                print("=" * 50)
                
                # Translate to current dialect if not PostgreSQL
                if self.current_dialect != 'postgresql':
                    print(f"\n🔄 Translating to {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}...")
                    translation_result = self.dialect_translator.translate_query(sql_query, self.current_dialect)
                    
                    if translation_result['success']:
                        print(f"\n📝 Translated SQL ({translation_result['dialect_name']}):")
                        print("=" * 50)
                        print(translation_result['translated_sql'])
                        print("=" * 50)
                        
                        if translation_result['translation_notes']:
                            print(f"💡 Translation notes: {', '.join(translation_result['translation_notes'])}")
                        
                        # Use translated query for execution
                        execution_sql = translation_result['translated_sql']
                    else:
                        print(f"❌ Translation failed: {translation_result['error']}")
                        print("Using original PostgreSQL query for execution")
                        execution_sql = sql_query
                else:
                    execution_sql = sql_query
                
                # Ask about actions
                print(f"\n🎯 Available actions:")
                print("1. Execute query")
                print("2. Translate to all dialects")
                print("3. Save query")
                print("4. Skip")
                
                action = input("Choose action [1-4] or press Enter for 1: ").strip()
                
                if action == '' or action == '1':
                    # Execute query
                    success = self.execute_query(execution_sql)
                    status = "executed" if success else "failed"
                elif action == '2':
                    # Translate to all dialects
                    self.translate_to_all_dialects(sql_query)
                    status = "translated"
                elif action == '3':
                    # Save query
                    self.save_query(question, sql_query, execution_sql if execution_sql != sql_query else None)
                    status = "saved"
                else:
                    status = "generated"
                
                # Record in history
                self.session_queries.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'question': question,
                    'sql': sql_query,
                    'dialect': self.current_dialect,
                    'status': status,
                    'confidence': confidence_display
                })
                
                return True
                
            else:
                print(f"❌ Query generation failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
            return False
    
    def execute_query(self, sql_query):
        """Execute query with enhanced formatting"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            if results:
                print(f"\n📊 Query Results ({len(results)} rows):")
                print("=" * 70)
                
                # Calculate column widths
                col_widths = []
                for i, col in enumerate(columns):
                    max_width = len(col)
                    for row in results[:10]:
                        if row[i] is not None:
                            max_width = max(max_width, len(str(row[i])))
                    col_widths.append(min(max_width, 20))
                
                # Display results
                header = " | ".join(col.ljust(width) for col, width in zip(columns, col_widths))
                print(header)
                print("-" * len(header))
                
                for row in results[:10]:
                    formatted_row = []
                    for val, width in zip(row, col_widths):
                        if val is None:
                            formatted_val = "NULL".ljust(width)
                        else:
                            val_str = str(val)
                            if len(val_str) > width:
                                formatted_val = val_str[:width-3] + "..."
                            else:
                                formatted_val = val_str.ljust(width)
                        formatted_row.append(formatted_val)
                    print(" | ".join(formatted_row))
                
                if len(results) > 10:
                    print(f"\n... and {len(results) - 10} more rows")
                    
                print("=" * 70)
            else:
                print("📋 Query executed successfully (no results returned)")
                
            cursor.close()
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Query execution error: {e}")
            self.connection.rollback()
            return False
    
    def save_query(self, question, original_sql, translated_sql=None):
        """Save query with dialect information"""
        try:
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = exports_dir / f"query_{timestamp}.sql"
            
            with open(filename, 'w') as f:
                f.write(f"-- SQL RAG Translator Export\n")
                f.write(f"-- Multi-Dialect Interactive CLI v3.0\n")
                f.write(f"-- Question: {question}\n")
                f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {self.db_config['database']} (PostgreSQL)\n")
                f.write(f"-- Target Dialect: {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}\n\n")
                
                f.write(f"-- Original PostgreSQL Query:\n")
                f.write(original_sql)
                
                if translated_sql and translated_sql != original_sql:
                    f.write(f"\n\n-- Translated to {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}:\n")
                    f.write(translated_sql)
            
            print(f"💾 Query saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False
    
    def display_history(self):
        """Display session history with dialect info"""
        if not self.session_queries:
            print("📝 No queries in this session yet")
            return
            
        print(f"\n📚 Query History ({len(self.session_queries)} queries):")
        print("=" * 70)
        for i, query_info in enumerate(self.session_queries, 1):
            status_emoji = "✅" if query_info['status'] == "executed" else "📝" if query_info['status'] == "generated" else "🔄"
            dialect_info = self.dialect_translator.get_dialect_info(query_info['dialect'])
            print(f"{i}. {status_emoji} {query_info['timestamp']} - {query_info['status'].upper()} ({dialect_info['name']})")
            print(f"   Q: {query_info['question']}")
            if i < len(self.session_queries):
                print()
    
    def run(self):
        """Enhanced main interactive loop"""
        if not self.connect_database():
            return
            
        if not self.initialize_components():
            return
        
        self.display_welcome()
        
        try:
            while True:
                print()
                user_input = input("💬 Enter your question: ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() in ['quit', 'exit']:
                    print(f"\n👋 Session complete! Generated {len(self.session_queries)} queries.")
                    print("Thanks for using SQL RAG Translator!")
                    break
                elif user_input.lower() == 'help':
                    self.display_help()
                    continue
                elif user_input.lower() == 'dialects':
                    self.display_dialect_menu()
                    continue
                elif user_input.lower() == 'history':
                    self.display_history()
                    continue
                elif user_input.lower() == 'schema':
                    self.display_schema_info()
                    continue
                elif user_input.lower().startswith('translate '):
                    # Extract SQL from translate command
                    sql_to_translate = user_input[10:].strip()
                    if sql_to_translate:
                        self.translate_to_all_dialects(sql_to_translate)
                    else:
                        print("❌ Please provide SQL query to translate")
                    continue
                
                # Process the question
                self.process_question(user_input)
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Session interrupted. Generated {len(self.session_queries)} queries total.")
            print("Goodbye!")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            if self.connection:
                self.connection.close()
                print("🔌 Database connection closed")


def main():
    """Entry point"""
    generator = MultiDialectInteractiveSQLGenerator()
    generator.run()


if __name__ == "__main__":
    main()