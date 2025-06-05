cat > test_query_fixes.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to validate query generator fixes
"""

import os
import sys
sys.path.append('src/sql')

from query_generator import NLToSQLGenerator

def test_fixes():
    """Test the improved query generator"""
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    generator = NLToSQLGenerator(
        schema_file_path='data/schemas/schema_analysis.json',
        anthropic_api_key=api_key
    )
    
    # Test the previously failing query
    failing_query = "List all customers from California with their total account balances"
    
    print("🧪 Testing Previously Failing Query:")
    print(f"❓ {failing_query}")
    print("─" * 60)
    
    result = generator.generate_sql_query(failing_query, 'postgresql')
    
    if result['success']:
        print("✅ SUCCESS! SQL extraction working:")
        print(result['sql_query'])
        print(f"\n📝 Explanation: {result['explanation']}")
        print(f"🎯 Confidence: {result['confidence']}")
        print(f"📊 Tables: {', '.join(result['relevant_tables'])}")
        
        # Check if we got actual SQL (not the error message)
        if "Could not extract SQL query" not in result['sql_query']:
            print("🎉 SQL Parser Fix: SUCCESSFUL")
        else:
            print("❌ SQL Parser Fix: FAILED")
            
    else:
        print(f"❌ Error: {result['error']}")
    
    print("\n" + "=" * 60)
    
    # Test a few more queries to ensure no regression
    test_queries = [
        "Show me employees earning more than $120,000",
        "Which branches are in Texas?",
        "What's the total transaction volume by month?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        result = generator.generate_sql_query(query, 'postgresql')
        
        if result['success'] and "Could not extract SQL query" not in result['sql_query']:
            print("✅ PASS")
        else:
            print("❌ FAIL")

if __name__ == "__main__":
    test_fixes()
EOF