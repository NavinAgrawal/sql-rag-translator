#!/usr/bin/env python3
"""
Enhanced Interactive SQL RAG Query Generator
Improved CLI with better schema context and formatting

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
    import psycopg2
    from psycopg2 import sql
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root and have installed dependencies")
    sys.exit(1)


class EnhancedInteractiveSQLGenerator:
    """Enhanced Interactive CLI for SQL query generation"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'banking_rag_db',
            'user': os.getenv('USER'),  # Use current macOS user
            'password': ''  # No password for local development
        }
        self.connection = None
        self.schema_analyzer = None
        self.query_generator = None
        self.session_queries = []
        self.enhanced_schema_info = None
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
        """Initialize schema analyzer and query generator with enhanced context"""
        try:
            # Initialize schema analyzer with connection
            self.schema_analyzer = SchemaAnalyzer(self.connection)
            schema_info = self.schema_analyzer.extract_complete_schema()
            
            # Enhance schema with relationship context
            self.enhanced_schema_info = self.enhance_schema_context(schema_info)
            
            # Save enhanced schema to file for NLToSQLGenerator
            schema_file = "data/schemas/enhanced_schema_analysis.json"
            os.makedirs("data/schemas", exist_ok=True)
            
            with open(schema_file, 'w') as f:
                json.dump(self.enhanced_schema_info, f, indent=2)
            
            # Get API key from environment
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("❌ ANTHROPIC_API_KEY not found in environment")
                print("Please set your API key: export ANTHROPIC_API_KEY='your-key-here'")
                return False
            
            # Initialize query generator with enhanced schema
            self.query_generator = NLToSQLGenerator(schema_file, api_key)
            
            print(f"📊 Schema loaded: {len(schema_info['tables'])} tables with enhanced relationships")
            return True
        except Exception as e:
            print(f"❌ Component initialization failed: {e}")
            return False
    
    def display_welcome(self):
        """Display enhanced welcome screen"""
        print("\n" + "="*65)
        print("🏦 SQL RAG Translator - Enhanced Interactive Mode")
        print("="*65)
        print(f"📅 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Database: {self.db_config['database']} (PostgreSQL)")
        print(f"🧠 Enhanced schema context with relationship paths")
        print("💡 Type 'help' for examples, 'quit' to exit")
        print("-"*65)
    
    def display_help(self):
        """Display enhanced help with better examples"""
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
        print("- 'history' - Show query history") 
        print("- 'schema' - Show table relationships")
        print("- 'quit' or 'exit' - Exit the application")
        print("-" * 50)
    
    def display_schema_info(self):
        """Display key schema relationships"""
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
    
    def display_history(self):
        """Display enhanced query history"""
        if not self.session_queries:
            print("📝 No queries in this session yet")
            return
            
        print(f"\n📚 Query History ({len(self.session_queries)} queries):")
        print("=" * 60)
        for i, query_info in enumerate(self.session_queries, 1):
            status_emoji = "✅" if query_info['status'] == "executed" else "📝" if query_info['status'] == "generated" else "❌"
            print(f"{i}. {status_emoji} {query_info['timestamp']} - {query_info['status'].upper()}")
            print(f"   Q: {query_info['question']}")
            if i < len(self.session_queries):
                print()
    
    def execute_query(self, sql_query):
        """Execute SQL query with enhanced result formatting"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            # Get results
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Enhanced result display
            if results:
                print(f"\n📊 Query Results ({len(results)} rows):")
                print("=" * 70)
                
                # Calculate column widths for better formatting
                col_widths = []
                for i, col in enumerate(columns):
                    max_width = len(col)
                    for row in results[:10]:  # Check first 10 rows
                        if row[i] is not None:
                            max_width = max(max_width, len(str(row[i])))
                    col_widths.append(min(max_width, 20))  # Cap at 20 chars
                
                # Header
                header = " | ".join(col.ljust(width) for col, width in zip(columns, col_widths))
                print(header)
                print("-" * len(header))
                
                # Data rows
                for row in results[:10]:  # Limit to first 10 rows
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
            self.connection.commit()  # Commit successful queries
            return True
            
        except Exception as e:
            print(f"❌ Query execution error: {e}")
            self.connection.rollback()  # Rollback failed queries
            return False
    
    def save_query(self, question, sql_query):
        """Save query with enhanced metadata"""
        try:
            # Create exports directory if it doesn't exist
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = exports_dir / f"query_{timestamp}.sql"
            
            # Write query with enhanced metadata
            with open(filename, 'w') as f:
                f.write(f"-- SQL RAG Translator Export\n")
                f.write(f"-- Generated by: Enhanced Interactive CLI v2.0\n")
                f.write(f"-- Question: {question}\n")
                f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {self.db_config['database']} (PostgreSQL)\n")
                f.write(f"-- Schema: 17 tables with enhanced relationship context\n\n")
                f.write(sql_query)
            
            print(f"💾 Query saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False
    
    def process_question(self, question):
        """Process question with enhanced error handling and feedback"""
        print(f"\n🤖 Generating SQL query...")
        
        try:
            # Generate SQL using enhanced query generator
            result = self.query_generator.generate_sql_query(question)
            
            if result['success']:
                sql_query = result['sql_query']
                # Try to get confidence from result, default to "Not available" if missing
                confidence = result.get('confidence_score', result.get('confidence', 'Not available'))
                
                if isinstance(confidence, (int, float)):
                    confidence_display = f"{confidence:.1%}"
                else:
                    confidence_display = str(confidence)
                
                print(f"✅ Query generated successfully! (Confidence: {confidence_display})")
                print(f"\n📝 Generated SQL (PostgreSQL):")
                print("=" * 50)
                print(sql_query)
                print("=" * 50)
                
                # Ask if user wants to execute
                execute = input("\n⚡ Execute query? [Y/n]: ").strip().lower()
                if execute in ['', 'y', 'yes']:
                    success = self.execute_query(sql_query)
                    status = "executed" if success else "failed"
                else:
                    status = "generated"
                
                # Ask if user wants to save
                save = input("💾 Save query? [Y/n]: ").strip().lower()
                if save in ['', 'y', 'yes']:
                    self.save_query(question, sql_query)
                
                # Record in session history
                self.session_queries.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'question': question,
                    'sql': sql_query,
                    'status': status,
                    'confidence': confidence_display
                })
                
                return True
                
            else:
                print(f"❌ Query generation failed: {result.get('error', 'Unknown error')}")
                print("💡 Try rephrasing your question or check 'help' for examples")
                return False
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
            print("💡 This might be a temporary issue. Please try again.")
            return False
    
    def run(self):
        """Enhanced main interactive loop"""
        # Initialize
        if not self.connect_database():
            return
            
        if not self.initialize_components():
            return
        
        self.display_welcome()
        
        # Main loop
        try:
            while True:
                print()
                question = input("💬 Enter your question: ").strip()
                
                if not question:
                    continue
                    
                # Handle commands
                if question.lower() in ['quit', 'exit']:
                    print(f"\n👋 Session complete! Generated {len(self.session_queries)} queries.")
                    print("Thanks for using SQL RAG Translator!")
                    break
                elif question.lower() == 'help':
                    self.display_help()
                    continue
                elif question.lower() == 'history':
                    self.display_history()
                    continue
                elif question.lower() == 'schema':
                    self.display_schema_info()
                    continue
                
                # Process the question
                self.process_question(question)
                
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
    generator = EnhancedInteractiveSQLGenerator()
    generator.run()


if __name__ == "__main__":
    main()