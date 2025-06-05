# Create and run the verification script
cat > test_complex_queries.py << 'EOF'
#!/usr/bin/env python3
import psycopg2

def test_queries():
    conn = psycopg2.connect(host='localhost', database='banking_rag_db', user='nba')
    cursor = conn.cursor()
    
    # Test 1: Multi-table join across geography
    print("🔍 Test 1: Top 5 cities by total deposits")
    cursor.execute("""
        SELECT ci.city_name, st.state_name, 
               COUNT(a.account_id) as accounts,
               SUM(a.current_balance) as total_deposits
        FROM cities ci
        JOIN states st ON ci.state_id = st.state_id
        LEFT JOIN customers c ON ci.city_id = c.city_id
        LEFT JOIN accounts a ON c.customer_id = a.customer_id
        GROUP BY ci.city_id, ci.city_name, st.state_name
        HAVING SUM(a.current_balance) > 0
        ORDER BY total_deposits DESC
        LIMIT 5;
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}, {row[1]}: {row[2]} accounts, ${row[3]:,.2f}")
    
    # Test 2: Employee hierarchy analysis
    print("\n🔍 Test 2: Management hierarchy")
    cursor.execute("""
        SELECT e.first_name || ' ' || e.last_name as employee,
               m.first_name || ' ' || m.last_name as manager,
               d.department_name,
               e.salary
        FROM employees e
        LEFT JOIN employees m ON e.manager_id = m.employee_id
        JOIN departments d ON e.department_id = d.department_id
        WHERE e.manager_id IS NOT NULL
        ORDER BY e.salary DESC
        LIMIT 5;
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]} reports to {row[1]} ({row[2]}) - ${row[3]:,}")
    
    print(f"\n✅ Database is ready for RAG system testing!")
    conn.close()

if __name__ == "__main__":
    test_queries()
EOF