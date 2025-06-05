#!/usr/bin/env python3
"""
Interactive SQL RAG Query Generator
Basic CLI interface for natural language to SQL translation

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


class InteractiveSQLGenerator:
    """Interactive CLI for SQL query generation"""
    
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
        print(f"🔧 Database config: user='{self.db_config['user']}', database='{self.db_config['database']}'")  # Debug info
        
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
    
    def initialize_components(self):
        """Initialize schema analyzer and query generator"""
        try:
            # Initialize schema analyzer with connection
            self.schema_analyzer = SchemaAnalyzer(self.connection)
            schema_info = self.schema_analyzer.extract_complete_schema()
            
            # Save schema to a temporary file for NLToSQLGenerator
            schema_file = "data/schemas/schema_analysis.json"
            os.makedirs("data/schemas", exist_ok=True)
            
            with open(schema_file, 'w') as f:
                import json
                json.dump(schema_info, f, indent=2)
            
            # Get API key from environment
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("❌ ANTHROPIC_API_KEY not found in environment")
                print("Please set your API key: export ANTHROPIC_API_KEY='your-key-here'")
                return False
            
            # Initialize query generator
            self.query_generator = NLToSQLGenerator(schema_file, api_key)
            
            print(f"📊 Schema loaded: {len(schema_info['tables'])} tables")
            return True
        except Exception as e:
            print(f"❌ Component initialization failed: {e}")
            return False
    
    def display_welcome(self):
        """Display welcome screen"""
        print("\n" + "="*60)
        print("🏦 SQL RAG Translator - Interactive Mode")
        print("="*60)
        print(f"📅 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Database: {self.db_config['database']} (PostgreSQL)")
        print("💡 Type 'help' for examples, 'quit' to exit")
        print("-"*60)
    
    def display_help(self):
        """Display help and example queries"""
        print("\n📚 Example Queries:")
        print("=" * 40)
        examples = [
            "Show me the top 5 customers by account balance",
            "List all customers from California with their total balances",
            "Which branch has the most employees?",
            "Show me employees who earn more than $100,000",
            "What are the different account types available?",
            "How many transactions were processed last month?"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example}")
        
        print("\n🎮 Commands:")
        print("- 'help' - Show this help")
        print("- 'history' - Show query history")
        print("- 'quit' or 'exit' - Exit the application")
        print("-" * 40)
    
    def display_history(self):
        """Display query history"""
        if not self.session_queries:
            print("📝 No queries in this session yet")
            return
            
        print(f"\n📚 Query History ({len(self.session_queries)} queries):")
        print("=" * 50)
        for i, query_info in enumerate(self.session_queries, 1):
            print(f"{i}. {query_info['timestamp']}")
            print(f"   Q: {query_info['question']}")
            print(f"   Status: {query_info['status']}")
            if i < len(self.session_queries):
                print()
    
    def execute_query(self, sql_query):
        """Execute SQL query and display results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            # Get results
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Display results
            if results:
                print(f"\n📊 Query Results ({len(results)} rows):")
                print("-" * 50)
                
                # Simple table display
                print(" | ".join(columns))
                print("-" * (len(" | ".join(columns))))
                
                for row in results[:10]:  # Limit to first 10 rows
                    print(" | ".join(str(val) for val in row))
                
                if len(results) > 10:
                    print(f"... and {len(results) - 10} more rows")
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
        """Save query to export file"""
        try:
            # Create exports directory if it doesn't exist
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = exports_dir / f"query_{timestamp}.sql"
            
            # Write query with metadata
            with open(filename, 'w') as f:
                f.write(f"-- SQL RAG Translator Export\n")
                f.write(f"-- Question: {question}\n")
                f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {self.db_config['database']}\n\n")
                f.write(sql_query)
            
            print(f"💾 Query saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False
    
    def process_question(self, question):
        """Process a natural language question"""
        print(f"\n🤖 Generating SQL query...")
        
        try:
            # Generate SQL using our existing query generator
            result = self.query_generator.generate_sql_query(question)
            
            if result['success']:
                sql_query = result['sql_query']
                confidence = result.get('confidence_score', 0)
                
                print(f"✅ Query generated successfully! (Confidence: {confidence:.1%})")
                print(f"\n📝 Generated SQL:")
                print("-" * 40)
                print(sql_query)
                print("-" * 40)
                
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
                    'status': status
                })
                
                return True
                
            else:
                print(f"❌ Query generation failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
            return False
    
    def run(self):
        """Main interactive loop"""
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
                    print("\n👋 Thanks for using SQL RAG Translator!")
                    break
                elif question.lower() == 'help':
                    self.display_help()
                    continue
                elif question.lower() == 'history':
                    self.display_history()
                    continue
                
                # Process the question
                self.process_question(question)
                
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            if self.connection:
                self.connection.close()
                print("🔌 Database connection closed")


def main():
    """Entry point"""
    generator = InteractiveSQLGenerator()
    generator.run()


if __name__ == "__main__":
    main()