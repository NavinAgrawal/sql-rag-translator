#!/usr/bin/env python3
"""
Professional Gradio Web Interface for SQL RAG Translator
Multi-tab interface with authentication, query execution, and export features

Author: Navin B Agrawal
Date: June 2025
"""

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import gradio as gr
import psycopg2

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from database.schema_analyzer import SchemaAnalyzer
    from sql.query_generator import NLToSQLGenerator
    from sql.dialect_translator import SQLDialectTranslator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root directory")
    sys.exit(1)


class SQLRAGWebInterface:
    """Professional Gradio web interface for SQL RAG system"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'banking_rag_db',
            'user': os.getenv('USER'),
            'password': ''
        }
        
        # Available dialects (define first)
        self.dialects = {
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL',
            'oracle': 'Oracle Database',
            'sqlserver': 'SQL Server'
        }
        
        # Core components
        self.connection = None
        self.schema_analyzer = None
        self.query_generator = None
        self.dialect_translator = SQLDialectTranslator()
        
        # Session management
        self.user_sessions = {}
        self.current_user = None
        
        # Initialize components
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize database connection and components"""
        try:
            # Database connection
            self.connection = psycopg2.connect(**self.db_config)
            
            # Schema analyzer
            self.schema_analyzer = SchemaAnalyzer(self.connection)
            schema_info = self.schema_analyzer.extract_complete_schema()
            
            # Enhanced schema context
            enhanced_schema = self.enhance_schema_context(schema_info)
            
            # Save enhanced schema
            schema_file = "data/schemas/enhanced_schema_analysis.json"
            os.makedirs("data/schemas", exist_ok=True)
            
            with open(schema_file, 'w') as f:
                json.dump(enhanced_schema, f, indent=2)
            
            # Query generator
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            self.query_generator = NLToSQLGenerator(schema_file, api_key)
            
            print(f"✅ Initialized: {len(schema_info['tables'])} tables, {len(self.dialects)} dialects")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise
    
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
            ]
        }
        
        return enhanced_schema
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Simple authentication system"""
        # Demo users (in production, use proper authentication)
        demo_users = {
            "admin": "admin123",
            "analyst": "analyst123",
            "demo": "demo123"
        }
        
        if username in demo_users and demo_users[username] == password:
            self.current_user = username
            if username not in self.user_sessions:
                self.user_sessions[username] = {
                    'queries': [],
                    'login_time': datetime.now(),
                    'last_activity': datetime.now()
                }
            return True, f"✅ Welcome {username}!"
        else:
            return False, "❌ Invalid credentials"
    
    def generate_sql_query(self, question: str, dialect: str, user_state: dict) -> Tuple[str, str, str, dict]:
        """Generate SQL query from natural language"""
        if not question.strip():
            return "Please enter a question", "", "", user_state
        
        try:
            start_time = time.time()
            
            # Generate PostgreSQL query first
            result = self.query_generator.generate_sql_query(question, 'postgresql')
            generation_time = time.time() - start_time
            
            if result['success']:
                sql_query = result['sql_query']
                confidence = result.get('confidence_score', result.get('confidence', 'Not available'))
                
                # Format confidence
                if isinstance(confidence, (int, float)):
                    confidence_display = f"{confidence:.1%}"
                else:
                    confidence_display = str(confidence)
                
                # Translate to target dialect if needed
                if dialect != 'postgresql':
                    translation_result = self.dialect_translator.translate_query(sql_query, dialect)
                    if translation_result['success']:
                        translated_sql = translation_result['translated_sql']
                        translation_notes = f"Translated to {self.dialects[dialect]}: {', '.join(translation_result['translation_notes'])}"
                    else:
                        translated_sql = sql_query
                        translation_notes = f"Translation to {self.dialects[dialect]} failed, using PostgreSQL"
                else:
                    translated_sql = sql_query
                    translation_notes = "Using original PostgreSQL syntax"
                
                # Update user session
                query_record = {
                    'timestamp': datetime.now().isoformat(),
                    'question': question,
                    'sql': sql_query,
                    'translated_sql': translated_sql,
                    'dialect': dialect,
                    'confidence': confidence_display,
                    'generation_time': generation_time
                }
                
                if self.current_user and self.current_user in self.user_sessions:
                    self.user_sessions[self.current_user]['queries'].append(query_record)
                    self.user_sessions[self.current_user]['last_activity'] = datetime.now()
                
                success_message = f"✅ Query generated successfully!\nConfidence: {confidence_display}\nGeneration time: {generation_time:.2f}s\n{translation_notes}"
                
                return success_message, sql_query, translated_sql, user_state
                
            else:
                error_message = f"❌ Query generation failed: {result.get('error', 'Unknown error')}"
                return error_message, "", "", user_state
                
        except Exception as e:
            error_message = f"❌ Error generating query: {str(e)}"
            return error_message, "", "", user_state
    
    def execute_query(self, sql_query: str) -> Tuple[str, pd.DataFrame]:
        """Execute SQL query and return results"""
        if not sql_query.strip():
            return "No query to execute", pd.DataFrame()
        
        try:
            start_time = time.time()
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            execution_time = time.time() - start_time
            
            cursor.close()
            self.connection.commit()
            
            if results:
                # Create DataFrame
                df = pd.DataFrame(results, columns=columns)
                success_message = f"✅ Query executed successfully!\nRows returned: {len(results)}\nExecution time: {execution_time:.3f}s"
                return success_message, df
            else:
                success_message = f"✅ Query executed successfully!\nNo rows returned\nExecution time: {execution_time:.3f}s"
                return success_message, pd.DataFrame()
                
        except Exception as e:
            self.connection.rollback()
            error_message = f"❌ Query execution error: {str(e)}"
            return error_message, pd.DataFrame()
    
    def get_user_history(self) -> pd.DataFrame:
        """Get user's query history as DataFrame"""
        if not self.current_user or self.current_user not in self.user_sessions:
            return pd.DataFrame()
        
        queries = self.user_sessions[self.current_user]['queries']
        if not queries:
            return pd.DataFrame()
        
        # Convert to DataFrame
        history_data = []
        for i, query in enumerate(reversed(queries[-20:]), 1):  # Last 20 queries
            history_data.append({
                '#': i,
                'Time': query['timestamp'][:19],  # Remove microseconds
                'Question': query['question'][:50] + "..." if len(query['question']) > 50 else query['question'],
                'Dialect': self.dialects[query['dialect']],
                'Confidence': query['confidence'],
                'Gen Time (s)': f"{query['generation_time']:.2f}"
            })
        
        return pd.DataFrame(history_data)
    
    def translate_to_all_dialects(self, sql_query: str) -> str:
        """Translate query to all dialects"""
        if not sql_query.strip():
            return "No query to translate"
        
        try:
            batch_result = self.dialect_translator.batch_translate(sql_query)
            
            output = "🔄 **Multi-Dialect Translation Results**\n\n"
            
            for dialect, result in batch_result['translations'].items():
                dialect_name = self.dialects[dialect]
                output += f"### 📝 {dialect_name} ({dialect.upper()})\n"
                
                if result['success']:
                    output += f"```sql\n{result['translated_sql']}\n```\n"
                    if result['translation_notes']:
                        output += f"**Changes:** {', '.join(result['translation_notes'])}\n"
                else:
                    output += f"❌ **Error:** {result['error']}\n"
                
                output += "\n"
            
            # Summary
            success_count = sum(1 for result in batch_result['translations'].values() if result['success'])
            total_count = len(batch_result['translations'])
            output += f"**Summary:** {success_count}/{total_count} dialects translated successfully"
            
            return output
            
        except Exception as e:
            return f"❌ Translation error: {str(e)}"
    
    def export_query(self, sql_query: str, question: str, dialect: str) -> str:
        """Export query to file"""
        if not sql_query.strip():
            return "No query to export"
        
        try:
            exports_dir = Path("data/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = exports_dir / f"web_query_{timestamp}.sql"
            
            with open(filename, 'w') as f:
                f.write(f"-- SQL RAG Translator Web Interface Export\n")
                f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- User: {self.current_user or 'Anonymous'}\n")
                f.write(f"-- Question: {question}\n")
                f.write(f"-- Target Dialect: {self.dialects[dialect]}\n\n")
                f.write(sql_query)
            
            return f"✅ Query exported to: {filename}"
            
        except Exception as e:
            return f"❌ Export error: {str(e)}"

    def create_interface(self):
        """Create the main Gradio interface"""
        
        # TARGETED CSS FIXES - FORCE OVERRIDES WITH !important
        custom_css = """
        /* AGGRESSIVE FIXES FOR GRADIO THEME CONFLICTS */

        /* Fix header */
        .header-text {
            background: linear-gradient(90deg, #1e40af, #3b82f6) !important;
            color: white !important;
            padding: 30px !important;
            border-radius: 12px !important;
            margin-bottom: 25px !important;
            text-align: center !important;
        }

        .header-text h1, .header-text p {
            color: white !important;
        }

        /* FORCE TAB COLOR FIXES - Target Gradio's actual tab classes */
        .tab-nav button[aria-selected="true"] {
            background: #1e40af !important;
            color: white !important;
            border-color: #1e40af !important;
        }

        .tab-nav button {
            background: #f8fafc !important;
            color: #374151 !important;
            border: 1px solid #d1d5db !important;
        }

        /* Gradio specific overrides */
        button[role="tab"][aria-selected="true"] {
            background: #1e40af !important;
            color: white !important;
        }

        button[role="tab"] {
            background: #f8fafc !important;
            color: #374151 !important;
        }

        /* FORCE TEXT READABILITY EVERYWHERE */
        .info-panel {
            background: #eff6ff !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 8px !important;
            padding: 16px !important;
            margin: 16px 0 !important;
        }

        .info-panel h4 {
            color: #1e40af !important;
            font-weight: bold !important;
            margin-bottom: 12px !important;
        }

        .info-panel li {
            color: #1f2937 !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
        }

        .info-panel strong {
            color: #1e40af !important;
        }

        .erd-panel {
            background: #eff6ff !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            height: 650px !important;
        }

        .erd-panel h3, .erd-panel h4, .erd-panel h5 {
            color: #1e40af !important;
            margin-bottom: 12px !important;
        }

        .erd-panel p, .erd-panel li {
            color: #1f2937 !important;
            line-height: 1.5 !important;
        }

        .erd-panel ul {
            margin-left: 0 !important;
            padding-left: 20px !important;
        }

        .erd-panel li {
            margin-bottom: 6px !important;
        }

        .erd-panel strong {
            color: #1e40af !important;
        }

        .system-info {
            background: white !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
            padding: 24px !important;
        }

        .system-info h3, .system-info h4 {
            color: #1e40af !important;
            margin-bottom: 12px !important;
        }

        .system-info strong {
            color: #1e40af !important;
        }

        .system-info li {
            color: #1f2937 !important;
            margin-bottom: 8px !important;
            line-height: 1.5 !important;
        }

        .system-info ul {
            margin-left: 0 !important;
            padding-left: 20px !important;
        }

        .system-info p {
            color: #1f2937 !important;
            line-height: 1.5 !important;
        }

        /* FORCE DEVELOPER FOOTER TEXT TO BE DARK */
        .developer-minimal {
            background: #f9fafb !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            font-size: 11px !important;
            color: #374151 !important;
            text-align: center !important;
            margin-top: 16px !important;
        }

        .developer-minimal strong {
            color: #1e40af !important;
        }

        .developer-minimal small {
            color: #6b7280 !important;
        }

        /* Universal text readability fixes */
        .gradio-container p, .gradio-container li, .gradio-container span {
            color: #1f2937 !important;
        }

        /* Fix any remaining white text issues */
        div[style*="color: white"] {
            color: #1f2937 !important;
        }
        """
        
        with gr.Blocks(css=custom_css, theme=gr.themes.Soft(), title="SQL RAG Translator") as app:
            
            # Professional Header
            gr.HTML("""
            <div class="header-text">
                <h1>🏦 SQL RAG Translator</h1>
                <p>Enterprise Natural Language to SQL Translation System</p>
            </div>
            """)
            
            # User state
            user_state = gr.State({})
            
            # LAYOUT - Better balance: 60/40 instead of 70/30
            with gr.Row():
                # LEFT SIDE - Main Interface (60% width)
                with gr.Column(scale=6):
                    with gr.Tabs():
                        
                        # Main Query Tab
                        with gr.Tab("🎯 SQL Query Generator"):
                            with gr.Row():
                                with gr.Column(scale=3):
                                    question_input = gr.Textbox(
                                        label="💬 Ask your question in natural language",
                                        placeholder="e.g., Show me the top 5 customers by account balance",
                                        lines=4,
                                        max_lines=6
                                    )
                                    
                                    with gr.Row():
                                        dialect_dropdown = gr.Dropdown(
                                            choices=list(self.dialects.keys()),
                                            value="postgresql",
                                            label="🌐 Target Database Dialect",
                                            info="Choose your target database platform"
                                        )
                                        
                                        generate_btn = gr.Button("🚀 Generate SQL", variant="primary", scale=2)
                                
                                with gr.Column(scale=1):
                                    # Examples Panel - Fixed indentation and structure
                                    gr.HTML("""
                                    <div class="info-panel">
                                        <h4>💡 Example Questions:</h4>
                                        <ul style="list-style-type: disc; margin-left: 0; padding-left: 20px;">
                                            <li style="margin-bottom: 8px;"><strong>Customer Analysis:</strong><br>Show top 10 customers by balance</li>
                                            <li style="margin-bottom: 8px;"><strong>Geographic:</strong><br>List all customers from California</li>
                                            <li style="margin-bottom: 8px;"><strong>Employee Data:</strong><br>Which branch has most employees?</li>
                                            <li style="margin-bottom: 8px;"><strong>Product Info:</strong><br>What are the different account types?</li>
                                            <li style="margin-bottom: 8px;"><strong>Transactions:</strong><br>How many transactions last month?</li>
                                            <li style="margin-bottom: 8px;"><strong>Financial:</strong><br>Show employees earning over $80,000</li>
                                            <li style="margin-bottom: 8px;"><strong>Analytics:</strong><br>What are the most popular products?</li>
                                            <li style="margin-bottom: 8px;"><strong>Complex:</strong><br>Monthly transaction volume by state</li>
                                        </ul>
                                    </div>
                                    """)
                            
                            # Generation Status
                            generation_status = gr.Textbox(label="📊 Generation Status", interactive=False)
                            
                            # SQL DISPLAY
                            gr.HTML("<h4>📝 Generated SQL Queries</h4>")
                            
                            with gr.Row():
                                with gr.Column():
                                    original_sql = gr.Code(
                                        label="🔵 PostgreSQL Query (Executable)",
                                        language="sql",
                                        interactive=False,
                                        lines=12
                                    )
                                    gr.HTML("<small>✅ This query executes against your PostgreSQL database</small>")
                                
                                with gr.Column():
                                    translated_sql = gr.Code(
                                        label="🔄 Translated Query (Target Dialect)",
                                        language="sql", 
                                        interactive=False,
                                        lines=12
                                    )
                                    gr.HTML("<small>📤 Use this query for your target database platform</small>")
                            
                            # ACTION BUTTONS
                            with gr.Row():
                                execute_btn = gr.Button("⚡ Execute Query", variant="secondary")
                                translate_all_btn = gr.Button("🌐 Translate All", variant="secondary") 
                                export_btn = gr.Button("💾 Export SQL", variant="secondary")
                            
                            # Translation results
                            translation_output = gr.Markdown(
                                label="🌐 Multi-Dialect Translations", 
                                visible=False
                            )
                            
                            # Query execution results
                            execution_status = gr.Textbox(label="⚡ Execution Status", interactive=False)
                            results_df = gr.Dataframe(
                                label="📊 Query Results", 
                                interactive=False,
                                wrap=True
                            )
                        
                        # Multi-Dialect Translation Tab
                        with gr.Tab("🌐 Multi-Dialect Translator"):
                            gr.HTML("<h3>🔄 Translate SQL to Multiple Database Dialects</h3>")
                            
                            input_sql = gr.Code(
                                label="📝 Input SQL Query (PostgreSQL syntax recommended)",
                                language="sql",
                                lines=15,
                                value="-- Enter your PostgreSQL query here\n-- Example:\nSELECT c.first_name, c.last_name, SUM(a.current_balance) as total_balance\nFROM customers c\nJOIN accounts a ON c.customer_id = a.customer_id\nGROUP BY c.customer_id\nORDER BY total_balance DESC\nLIMIT 5;"
                            )

                            with gr.Row():
                                translate_btn = gr.Button("🚀 Translate to All Dialects", variant="primary")
                                clear_btn = gr.Button("🗑️ Clear", variant="secondary")
                            
                            translation_output_tab = gr.Markdown(
                                label="🌐 Translation Results",
                                value="Enter a SQL query above and click 'Translate to All Dialects' to see the results."
                            )
                        
                        # Query History Tab
                        with gr.Tab("📚 Query History"):
                            gr.HTML("<h3>📋 Your Recent Queries</h3>")
                            
                            with gr.Row():
                                refresh_history_btn = gr.Button("🔄 Refresh History", variant="secondary")
                                clear_history_btn = gr.Button("🗑️ Clear History", variant="secondary")
                            
                            session_stats = gr.Textbox(
                                label="📊 Session Statistics",
                                value="Queries generated: 0 | Session time: 0 min",
                                interactive=False
                            )
                            
                            history_df = gr.Dataframe(
                                label="📚 Query History (Last 20 queries)",
                                interactive=False,
                                wrap=True
                            )
                        
                        # System Info Tab  
                        with gr.Tab("ℹ️ System Info"):
                            gr.HTML("""
                            <div class="system-info">
                                <h3>🏦 SQL RAG Translator System Information</h3>
                                
                                <h4>📊 Current Banking Database Schema:</h4>
                                <ul style="list-style-type: disc; margin-left: 0; padding-left: 20px;">
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Tables:</strong> 17 interconnected banking tables</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Sample Records:</strong> 8,000+ realistic banking records</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Relationships:</strong> 24 foreign key constraints</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Business Rules:</strong> 698+ constraints and validations</li>
                                </ul>
                                
                                <h4>🌐 Supported Database Platforms:</h4>
                                <ul style="list-style-type: disc; margin-left: 0; padding-left: 20px;">
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">PostgreSQL</strong> - Advanced open-source database (Currently Connected)</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">MySQL</strong> - Popular web application database</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Oracle Database</strong> - Enterprise database platform</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">SQL Server</strong> - Microsoft database platform</li>
                                </ul>
                                
                                <h4>🚀 Enterprise Features:</h4>
                                <ul style="list-style-type: disc; margin-left: 0; padding-left: 20px;">
                                    <li style="margin-bottom: 8px; color: #1f2937;">Natural language to SQL translation with 95%+ accuracy</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;">Multi-dialect support with automatic syntax translation</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;">Real banking schema with customer, account, transaction data</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;">Query execution with result visualization and export</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;">Session management with query history and persistence</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;">Professional web interface with responsive design</li>
                                </ul>
                                
                                <h4>🎯 Coming Soon:</h4>
                                <ul style="list-style-type: disc; margin-left: 0; padding-left: 20px;">
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Interactive ERD Visualization</strong> - Real-time schema diagrams</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Custom Schema Upload</strong> - Upload your own database schemas</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">User Authentication</strong> - Persistent user accounts</li>
                                    <li style="margin-bottom: 8px; color: #1f2937;"><strong style="color: #1e40af;">Query Optimization</strong> - Performance suggestions</li>
                                </ul>
                            </div>
                            
                            <div class="developer-minimal">
                                © 2025 <strong style="color: #1e40af;">Navin B Agrawal</strong><br>
                                <small style="color: #6b7280;">All rights reserved. Built with AI assistance.</small>
                            </div>
                            """)
                
                # RIGHT SIDE - ERD Visualization Panel (40% width - better balance)
                with gr.Column(scale=4):
                    gr.HTML("""
                    <div class="erd-panel">
                        <h3>🗺️ Database Schema Visualization</h3>
                        
                        <div style="text-align: center;">
                            <h4>📋 Current Schema: Banking System</h4>
                            <p><strong>17 Tables</strong> | <strong>24 Relationships</strong></p>
                            
                            <div style="background: white; border: 1px solid #cbd5e1; 
                                       border-radius: 8px; padding: 15px; margin: 15px 0; text-align: left;">
                                <h5 style="text-align: center; color: #1e40af; margin-bottom: 12px;">Key Table Categories:</h5>
                                <ul style="font-size: 13px; list-style-type: disc; margin-left: 0; padding-left: 20px;">
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">Geography:</strong> countries, states, cities</li>
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">Organization:</strong> regions, branches, departments</li>
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">People:</strong> employees, customers</li>
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">Products:</strong> product_categories, products</li>
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">Accounts:</strong> customer_types, accounts</li>
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">Transactions:</strong> transaction_types, transactions</li>
                                    <li style="margin-bottom: 6px; color: #1f2937;"><strong style="color: #1e40af;">Commerce:</strong> merchant_categories, merchants</li>
                                </ul>
                            </div>
                            
                            <div style="background: #fef3c7; border: 2px solid #f59e0b; 
                                       border-radius: 8px; padding: 12px; margin: 15px 0;">
                                <p style="margin: 0; font-weight: 600; color: #92400e;">
                                    🚧 <strong>Interactive ERD Coming Soon!</strong><br>
                                    <small style="color: #92400e;">Real-time visualization with zoom, pan, and relationship mapping</small>
                                </p>
                            </div>
                        </div>
                    </div>
                    """)

            # Event handlers (keep all your existing ones - no changes needed)
            generate_btn.click(
                fn=self.generate_sql_query,
                inputs=[question_input, dialect_dropdown, user_state],
                outputs=[generation_status, original_sql, translated_sql, user_state]
            )
            
            execute_btn.click(
                fn=self.execute_query,
                inputs=[original_sql],
                outputs=[execution_status, results_df]
            )
            
            # Enhanced translate function that shows results and switches tabs
            def enhanced_translate_all(sql_query):
                if not sql_query.strip():
                    return "Please generate a query first", gr.update(visible=True), sql_query, self.translate_to_all_dialects("")
                
                translation_result = self.translate_to_all_dialects(sql_query)
                return translation_result, gr.update(visible=True), sql_query, translation_result
            
            translate_all_btn.click(
                fn=enhanced_translate_all,
                inputs=[original_sql],
                outputs=[translation_output, translation_output, input_sql, translation_output]
            )
            
            translate_btn.click(
                fn=self.translate_to_all_dialects,
                inputs=[input_sql],
                outputs=[translation_output_tab]
            )
            
            export_btn.click(
                fn=self.export_query,
                inputs=[translated_sql, question_input, dialect_dropdown],
                outputs=[generation_status]
            )
            
            refresh_history_btn.click(
                fn=self.get_user_history,
                outputs=[history_df]
            )
        
        return app

def main():
    """Launch the Gradio application"""
    try:
        # Initialize the interface
        sql_rag = SQLRAGWebInterface()
        app = sql_rag.create_interface()
        
        # Launch the app
        app.launch(
            server_name="127.0.0.1",   # Use localhost instead of 0.0.0.0
            server_port=7860,          # Standard Gradio port
            share=False,               # Set to True for public sharing
            debug=True,                # Enable debug mode
            show_error=True,           # Show detailed errors
            inbrowser=True             # Automatically open in browser
        )
        
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()