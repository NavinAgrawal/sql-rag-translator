#!/usr/bin/env python3
"""
Enhanced Multi-Dialect Interactive SQL RAG Query Generator
Professional CLI with colors, performance metrics, and enhanced UX

Author: Navin B Agrawal
Date: June 2025
"""

import os
import sys
import json
import time
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
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.columns import Columns
    from rich.align import Align
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root and have installed dependencies")
    print("Run: pip install rich")
    sys.exit(1)


class ProfessionalInteractiveSQLGenerator:
    """Professional Interactive CLI with colors and performance metrics"""
    
    def __init__(self):
        self.console = Console()
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
        self.current_dialect = 'postgresql'
        self.session_start_time = time.time()
        
        # Performance metrics
        self.performance_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'total_generation_time': 0,
            'total_execution_time': 0
        }
        
        self.console.print(f"🔧 [cyan]Database config:[/] user='{self.db_config['user']}', database='{self.db_config['database']}'")
        
    def connect_database(self):
        """Establish database connection with progress"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Connecting to database...", total=None)
            
            try:
                self.connection = psycopg2.connect(**self.db_config)
                progress.update(task, description="✅ Connected to database")
                time.sleep(0.5)  # Brief pause to show success
                self.console.print(f"✅ [green]Connected to database:[/] {self.db_config['database']}")
                return True
            except Exception as e:
                progress.update(task, description="❌ Connection failed")
                self.console.print(f"❌ [red]Database connection failed:[/] {e}")
                self.console.print("[yellow]Make sure PostgreSQL is running and the database exists[/]")
                return False
    
    def enhance_schema_context(self, schema_info):
        """Enhance schema with relationship documentation"""
        enhanced_schema = schema_info.copy()
        
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
                'cities.state_id → states.state_id'
            ],
            'branch_employee_queries': [
                'branches.branch_id → employees.branch_id',
                'Filter active employees: WHERE employees.termination_date IS NULL'
            ]
        }
        
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
            }
        }
        
        return enhanced_schema
    
    def initialize_components(self):
        """Initialize components with progress indicators"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            # Schema analysis
            task1 = progress.add_task("Analyzing database schema...", total=None)
            try:
                self.schema_analyzer = SchemaAnalyzer(self.connection)
                schema_info = self.schema_analyzer.extract_complete_schema()
                progress.update(task1, description="✅ Schema analyzed")
                
                # Schema enhancement
                task2 = progress.add_task("Enhancing schema context...", total=None)
                self.enhanced_schema_info = self.enhance_schema_context(schema_info)
                
                schema_file = "data/schemas/enhanced_schema_analysis.json"
                os.makedirs("data/schemas", exist_ok=True)
                
                with open(schema_file, 'w') as f:
                    json.dump(self.enhanced_schema_info, f, indent=2)
                progress.update(task2, description="✅ Schema enhanced")
                
                # API key check
                task3 = progress.add_task("Checking API credentials...", total=None)
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    progress.update(task3, description="❌ API key missing")
                    self.console.print("❌ [red]ANTHROPIC_API_KEY not found in environment[/]")
                    return False
                progress.update(task3, description="✅ API key verified")
                
                # Query generator initialization
                task4 = progress.add_task("Initializing AI query generator...", total=None)
                self.query_generator = NLToSQLGenerator(schema_file, api_key)
                progress.update(task4, description="✅ AI generator ready")
                
                time.sleep(0.5)  # Brief pause to show completion
                
            except Exception as e:
                self.console.print(f"❌ [red]Component initialization failed:[/] {e}")
                return False
        
        self.console.print(f"📊 [green]Schema loaded:[/] {len(schema_info['tables'])} tables with enhanced relationships")
        self.console.print(f"🔄 [green]Dialect translator:[/] {len(self.dialect_translator.get_available_dialects())} dialects available")
        return True
    
    def display_welcome(self):
        """Display colorized welcome screen"""
        welcome_text = Text()
        welcome_text.append("🏦 SQL RAG Translator - Professional Interactive Mode", style="bold blue")
        
        info_table = Table.grid(padding=1)
        info_table.add_column(style="cyan", justify="right")
        info_table.add_column(style="white")
        
        info_table.add_row("📅 Session:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info_table.add_row("🗄️  Database:", f"{self.db_config['database']} (PostgreSQL)")
        info_table.add_row("🎯 Current dialect:", self.dialect_translator.get_dialect_info(self.current_dialect)['name'])
        info_table.add_row("🌐 Available dialects:", ", ".join(self.dialect_translator.get_available_dialects()))
        
        welcome_panel = Panel(
            Align.center(Columns([welcome_text, info_table], equal=True)),
            title="[bold green]Welcome[/]",
            border_style="blue"
        )
        
        self.console.print(welcome_panel)
        self.console.print("💡 [yellow]Commands:[/] 'help', 'dialects', 'schema', 'stats', 'quit'")
    
    def display_dialect_menu(self):
        """Display colorized dialect selection"""
        table = Table(title="🌐 Available Database Dialects", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=6)
        table.add_column("Database", style="green", width=15)
        table.add_column("Description", style="white")
        table.add_column("Status", style="yellow", width=10)
        
        dialects = self.dialect_translator.get_available_dialects()
        for i, dialect in enumerate(dialects, 1):
            info = self.dialect_translator.get_dialect_info(dialect)
            status = "✅ Current" if dialect == self.current_dialect else ""
            table.add_row(str(i), info['name'], info['description'], status)
        
        self.console.print(table)
        self.console.print("💡 [italic]Note: Queries are generated in PostgreSQL, then translated to other dialects[/]")
        
        try:
            choice = Prompt.ask(f"\n[cyan]Select dialect [1-{len(dialects)}] or press Enter to keep current[/]", default="")
            if choice:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(dialects):
                    old_dialect = self.current_dialect
                    self.current_dialect = dialects[choice_idx]
                    dialect_info = self.dialect_translator.get_dialect_info(self.current_dialect)
                    self.console.print(f"✅ [green]Switched from {old_dialect} to {dialect_info['name']}[/]")
                else:
                    self.console.print("❌ [red]Invalid choice[/]")
            else:
                current_info = self.dialect_translator.get_dialect_info(self.current_dialect)
                self.console.print(f"[yellow]Keeping current dialect: {current_info['name']}[/]")
        except ValueError:
            self.console.print("❌ [red]Invalid input[/]")
    
    def translate_to_all_dialects(self, sql_query):
        """Translate query to all dialects and display with colors"""
        self.console.print(f"\n🔄 [bold blue]Translating to all database dialects...[/]")
        
        batch_result = self.dialect_translator.batch_translate(sql_query)
        
        for dialect, result in batch_result['translations'].items():
            dialect_info = self.dialect_translator.get_dialect_info(dialect)
            
            # Create colored header
            dialect_text = Text()
            dialect_text.append(f"📝 {dialect_info['name']} ", style="bold green")
            dialect_text.append(f"({dialect.upper()})", style="cyan")
            self.console.print(f"\n{dialect_text}")
            
            if result['success']:
                # Display translated SQL with syntax highlighting
                translated_syntax = Syntax(result['translated_sql'], "sql", theme="monokai", line_numbers=True)
                self.console.print(Panel(translated_syntax, border_style="green", title=f"{dialect_info['name']}"))
                
                if result['translation_notes']:
                    notes_text = Text("💡 Changes: ", style="yellow")
                    notes_text.append(", ".join(result['translation_notes']), style="white")
                    self.console.print(notes_text)
            else:
                error_panel = Panel(
                    f"❌ Translation failed: {result['error']}",
                    border_style="red",
                    title="Error"
                )
                self.console.print(error_panel)
        
        # Summary
        success_count = sum(1 for result in batch_result['translations'].values() if result['success'])
        total_count = len(batch_result['translations'])
        
        summary_text = Text()
        summary_text.append(f"✅ Translation complete: ", style="green")
        summary_text.append(f"{success_count}/{total_count} dialects successful", style="cyan")
        self.console.print(f"\n{summary_text}")
    
    def save_query(self, question, original_sql, translated_sql=None):
        """Save query with enhanced metadata and colors"""
        try:
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = exports_dir / f"query_{timestamp}.sql"
            
            with open(filename, 'w') as f:
                f.write(f"-- SQL RAG Translator Export\n")
                f.write(f"-- Professional Interactive CLI v4.0\n")
                f.write(f"-- Question: {question}\n")
                f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {self.db_config['database']} (PostgreSQL)\n")
                f.write(f"-- Target Dialect: {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}\n\n")
                
                f.write(f"-- Original PostgreSQL Query:\n")
                f.write(original_sql)
                
                if translated_sql and translated_sql != original_sql:
                    f.write(f"\n\n-- Translated to {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}:\n")
                    f.write(translated_sql)
            
            save_text = Text()
            save_text.append("💾 Query saved to: ", style="green")
            save_text.append(str(filename), style="cyan")
            self.console.print(save_text)
            return True
            
        except Exception as e:
            self.console.print(f"❌ [red]Save error:[/] {e}")
            return False
        """Display session performance statistics"""
        session_duration = time.time() - self.session_start_time
        
        stats_table = Table(title="📊 Session Performance Statistics", show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="green")
        stats_table.add_column("Value", style="white", justify="right")
        stats_table.add_column("Average", style="yellow", justify="right")
        
        total_queries = self.performance_stats['total_queries']
        successful_queries = self.performance_stats['successful_queries']
        
        stats_table.add_row("Session Duration", f"{session_duration:.1f}s", "")
        stats_table.add_row("Total Queries", str(total_queries), "")
        stats_table.add_row("Successful Queries", str(successful_queries), f"{(successful_queries/total_queries*100) if total_queries > 0 else 0:.1f}%")
        
        if total_queries > 0:
            avg_generation = self.performance_stats['total_generation_time'] / total_queries
            avg_execution = self.performance_stats['total_execution_time'] / successful_queries if successful_queries > 0 else 0
            
            stats_table.add_row("Total Generation Time", f"{self.performance_stats['total_generation_time']:.2f}s", f"{avg_generation:.2f}s")
            stats_table.add_row("Total Execution Time", f"{self.performance_stats['total_execution_time']:.2f}s", f"{avg_execution:.2f}s")
        
        self.console.print(stats_table)
    
    def process_question(self, question):
        """Process question with performance timing and colors"""
        self.performance_stats['total_queries'] += 1
        
        # Start timing
        generation_start = time.time()
        
        # Show progress for generation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🤖 Generating SQL query...", total=None)
            
            try:
                result = self.query_generator.generate_sql_query(question, 'postgresql')
                generation_time = time.time() - generation_start
                self.performance_stats['total_generation_time'] += generation_time
                
                progress.update(task, description="✅ Query generated successfully!")
                time.sleep(0.3)
                
            except Exception as e:
                progress.update(task, description="❌ Generation failed")
                self.console.print(f"❌ [red]Error processing question:[/] {e}")
                return False
        
        # Process results outside of progress context
        try:
            if result['success']:
                sql_query = result['sql_query']
                confidence = result.get('confidence_score', result.get('confidence', 'Not available'))
                
                if isinstance(confidence, (int, float)):
                    confidence_display = f"{confidence:.1%}"
                else:
                    confidence_display = str(confidence)
                
                # Display generation success with timing
                success_text = Text()
                success_text.append("✅ Query generated successfully! ", style="green")
                success_text.append(f"(Confidence: {confidence_display}, ", style="cyan")
                success_text.append(f"Time: {generation_time:.2f}s)", style="cyan")
                self.console.print(success_text)
                
                # Display PostgreSQL query with syntax highlighting
                self.console.print("\n📝 [bold blue]Generated SQL (PostgreSQL):[/]")
                sql_syntax = Syntax(sql_query, "sql", theme="monokai", line_numbers=True)
                self.console.print(Panel(sql_syntax, border_style="blue"))
                
                # Handle dialect translation
                if self.current_dialect != 'postgresql':
                    self.console.print(f"\n🔄 [blue]Translating to {self.dialect_translator.get_dialect_info(self.current_dialect)['name']}...[/]")
                    
                    translation_result = self.dialect_translator.translate_query(sql_query, self.current_dialect)
                    
                    if translation_result['success']:
                        self.console.print(f"\n📝 [bold green]Translated SQL ({translation_result['dialect_name']}):[/]")
                        translated_syntax = Syntax(translation_result['translated_sql'], "sql", theme="monokai", line_numbers=True)
                        self.console.print(Panel(translated_syntax, border_style="green"))
                        
                        if translation_result['translation_notes']:
                            notes_text = Text("💡 Translation notes: ", style="yellow")
                            notes_text.append(", ".join(translation_result['translation_notes']), style="white")
                            self.console.print(notes_text)
                        
                        execution_sql = translation_result['translated_sql']
                    else:
                        self.console.print(f"❌ [red]Translation failed:[/] {translation_result['error']}")
                        self.console.print("[yellow]Using original PostgreSQL query for execution[/]")
                        execution_sql = sql_query
                else:
                    execution_sql = sql_query
                
                # Action menu with colors
                action_table = Table(show_header=False, box=None, padding=(0, 2))
                action_table.add_column(style="cyan")
                action_table.add_column(style="white")
                
                action_table.add_row("1.", "Execute query")
                action_table.add_row("2.", "Translate to all dialects")
                action_table.add_row("3.", "Save query")
                action_table.add_row("4.", "Skip")
                
                self.console.print("\n🎯 [bold]Available actions:[/]")
                self.console.print(action_table)
                
                action = Prompt.ask("[cyan]Choose action [1-4] or press Enter for 1[/]", default="1")
                
                if action in ['', '1']:
                    success = self.execute_query(execution_sql)
                    status = "executed" if success else "failed"
                    if success:
                        self.performance_stats['successful_queries'] += 1
                elif action == '2':
                    self.translate_to_all_dialects(sql_query)
                    status = "translated"
                elif action == '3':
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
                    'confidence': confidence_display,
                    'generation_time': generation_time
                })
                
                return True
                
            else:
                self.console.print(f"❌ [red]Query generation failed:[/] {result.get('error', 'Unknown error')}")
                self.console.print("💡 [yellow]Try rephrasing your question or check 'help' for examples[/]")
                return False
                
        except Exception as e:
            self.console.print(f"❌ [red]Error processing question:[/] {e}")
            return False
    
    def execute_query(self, sql_query):
        """Execute query with timing and enhanced table display"""
        execution_start = time.time()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            execution_time = time.time() - execution_start
            self.performance_stats['total_execution_time'] += execution_time
            
            if results:
                # Create rich table for results
                result_table = Table(
                    title=f"📊 Query Results ({len(results)} rows, {execution_time:.3f}s)",
                    show_header=True,
                    header_style="bold magenta"
                )
                
                # Add columns
                for col in columns:
                    result_table.add_column(col, style="white", overflow="ellipsis", max_width=20)
                
                # Add rows (limit to 10)
                for row in results[:10]:
                    formatted_row = []
                    for val in row:
                        if val is None:
                            formatted_row.append("[dim]NULL[/]")
                        else:
                            formatted_row.append(str(val))
                    result_table.add_row(*formatted_row)
                
                self.console.print(result_table)
                
                if len(results) > 10:
                    self.console.print(f"[yellow]... and {len(results) - 10} more rows[/]")
                    
            else:
                success_panel = Panel(
                    "Query executed successfully (no results returned)",
                    title="Success",
                    border_style="green"
                )
                self.console.print(success_panel)
                
            cursor.close()
            self.connection.commit()
            return True
            
        except Exception as e:
            self.console.print(f"❌ [red]Query execution error:[/] {e}")
            self.connection.rollback()
            return False
    
    def run(self):
        """Enhanced main loop with professional interface"""
        if not self.connect_database():
            return
            
        if not self.initialize_components():
            return
        
        self.display_welcome()
        
        try:
            while True:
                self.console.print()
                question = Prompt.ask("💬 [bold cyan]Enter your question[/]").strip()
                
                if not question:
                    continue
                    
                # Handle commands
                if question.lower() in ['quit', 'exit']:
                    self.console.print(f"\n👋 [green]Session complete![/] Generated {len(self.session_queries)} queries.")
                    self.display_performance_stats()
                    self.console.print("[blue]Thanks for using SQL RAG Translator![/]")
                    break
                elif question.lower() == 'help':
                    # Display help (simplified for space)
                    help_panel = Panel(
                        "📚 Try questions like:\n" +
                        "• Show me the top 5 customers by account balance\n" +
                        "• List all customers from California\n" +
                        "• Which branch has the most employees?\n\n" +
                        "🎮 Commands: 'dialects', 'schema', 'stats', 'quit'",
                        title="[bold]Help",
                        border_style="yellow"
                    )
                    self.console.print(help_panel)
                    continue
                elif question.lower() == 'dialects':
                    self.display_dialect_menu()
                    continue
                elif question.lower() == 'stats':
                    self.display_performance_stats()
                    continue
                elif question.lower() == 'schema':
                    schema_panel = Panel(
                        "📋 Key relationships:\n" +
                        "• Customers → Accounts → Transactions\n" +
                        "• Regions → Branches → Employees\n" +
                        "• Countries → States → Cities → Customers",
                        title="[bold]Schema Info",
                        border_style="cyan"
                    )
                    self.console.print(schema_panel)
                    continue
                
                # Process the question
                self.process_question(question)
                
        except KeyboardInterrupt:
            self.console.print(f"\n\n👋 [yellow]Session interrupted.[/] Generated {len(self.session_queries)} queries total.")
            self.console.print("[blue]Goodbye![/]")
        except Exception as e:
            self.console.print(f"\n❌ [red]Unexpected error:[/] {e}")
        finally:
            if self.connection:
                self.connection.close()
                self.console.print("🔌 [dim]Database connection closed[/]")


def main():
    """Entry point"""
    generator = ProfessionalInteractiveSQLGenerator()
    generator.run()


if __name__ == "__main__":
    main()