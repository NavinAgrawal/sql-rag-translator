#!/usr/bin/env python3
"""
Comprehensive Banking Data Generator
Generates realistic banking data with proper relationships and constraints
"""

import os
import sys
import random
import psycopg2
from faker import Faker
from datetime import datetime, timedelta, date
import decimal
from tqdm import tqdm
import argparse

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

fake = Faker('en_US')
fake.seed_instance(42)  # For reproducible data
random.seed(42)

class BankingDataGenerator:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
        
        # Data storage for referential integrity
        self.country_ids = []
        self.state_ids = []
        self.city_ids = []
        self.region_ids = []
        self.branch_ids = []
        self.department_ids = []
        self.employee_ids = []
        self.customer_segment_ids = []
        self.customer_type_ids = []
        self.customer_ids = []
        self.product_category_ids = []
        self.product_ids = []
        self.account_ids = []
        self.transaction_type_ids = []
        self.mcc_ids = []
        self.merchant_ids = []
        
    def generate_countries(self, count=10):
        """Generate country reference data"""
        print(f"🌍 Generating {count} countries...")
        
        countries_data = [
            ('USA', 'United States', 'USD', 0.0750),
            ('CAN', 'Canada', 'CAD', 0.0500),
            ('GBR', 'United Kingdom', 'GBP', 0.0200),
            ('DEU', 'Germany', 'EUR', 0.1900),
            ('FRA', 'France', 'EUR', 0.2000),
            ('JPN', 'Japan', 'JPY', 0.1000),
            ('AUS', 'Australia', 'AUD', 0.1000),
            ('CHE', 'Switzerland', 'CHF', 0.0750),
            ('NLD', 'Netherlands', 'EUR', 0.2100),
            ('SWE', 'Sweden', 'SEK', 0.2500),
        ]
        
        for code, name, currency, tax_rate in countries_data:
            self.cursor.execute("""
                INSERT INTO countries (country_code, country_name, currency_code, tax_rate)
                VALUES (%s, %s, %s, %s) RETURNING country_id;
            """, (code, name, currency, tax_rate))
            self.country_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.country_ids)} countries")

    def generate_states(self, count=50):
        """Generate US states and provinces"""
        print(f"🗺️  Generating {count} states...")
        
        us_states = [
            ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
            ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
            ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
            ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
            ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
            ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
            ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
            ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
            ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
            ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
            ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
            ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
            ('WI', 'Wisconsin'), ('WY', 'Wyoming')
        ]
        
        # USA is typically the first country
        usa_country_id = self.country_ids[0]
        
        for state_code, state_name in us_states:
            tax_rate = round(random.uniform(0.0000, 0.1250), 4)
            self.cursor.execute("""
                INSERT INTO states (country_id, state_code, state_name, tax_rate)
                VALUES (%s, %s, %s, %s) RETURNING state_id;
            """, (usa_country_id, state_code, state_name, tax_rate))
            self.state_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.state_ids)} states")

    def generate_cities(self, count=200):
        """Generate cities with realistic demographics"""
        print(f"🏙️  Generating {count} cities...")
        
        major_cities = [
            ('New York', 8400000, 65000), ('Los Angeles', 4000000, 62000),
            ('Chicago', 2700000, 58000), ('Houston', 2300000, 52000),
            ('Phoenix', 1600000, 55000), ('Philadelphia', 1600000, 45000),
            ('San Antonio', 1500000, 48000), ('San Diego', 1400000, 72000),
            ('Dallas', 1300000, 56000), ('San Jose', 1000000, 109000),
            ('Austin', 950000, 67000), ('Jacksonville', 900000, 52000),
            ('Fort Worth', 870000, 54000), ('Columbus', 850000, 51000),
            ('Charlotte', 850000, 58000), ('San Francisco', 875000, 112000),
            ('Indianapolis', 850000, 48000), ('Seattle', 750000, 85000),
            ('Denver', 715000, 62000), ('Washington', 700000, 75000)
        ]
        
        cities_created = 0
        
        # Add major cities first
        for city_name, population, median_income in major_cities:
            if cities_created >= count:
                break
                
            state_id = random.choice(self.state_ids)
            zip_code = fake.postcode()
            
            self.cursor.execute("""
                INSERT INTO cities (state_id, city_name, population, median_income, zip_code_primary)
                VALUES (%s, %s, %s, %s, %s) RETURNING city_id;
            """, (state_id, city_name, population, median_income, zip_code))
            self.city_ids.append(self.cursor.fetchone()[0])
            cities_created += 1
        
        # Generate remaining cities
        for _ in range(count - cities_created):
            state_id = random.choice(self.state_ids)
            city_name = fake.city()
            population = random.randint(10000, 500000)
            median_income = random.randint(35000, 85000)
            zip_code = fake.postcode()
            
            try:
                self.cursor.execute("""
                    INSERT INTO cities (state_id, city_name, population, median_income, zip_code_primary)
                    VALUES (%s, %s, %s, %s, %s) RETURNING city_id;
                """, (state_id, city_name, population, median_income, zip_code))
                self.city_ids.append(self.cursor.fetchone()[0])
            except psycopg2.IntegrityError:
                self.conn.rollback()
                continue  # Skip duplicate city names
        
        self.conn.commit()
        print(f"✅ Created {len(self.city_ids)} cities")

    def generate_regions(self, count=8):
        """Generate bank regions"""
        print(f"🏢 Generating {count} regions...")
        
        regions = [
            ('NORTHEAST', 'Northeast Region', 'John Smith'),
            ('SOUTHEAST', 'Southeast Region', 'Maria Garcia'),
            ('MIDWEST', 'Midwest Region', 'Robert Johnson'),
            ('SOUTHWEST', 'Southwest Region', 'Lisa Wong'),
            ('WEST', 'West Region', 'David Brown'),
            ('NORTHWEST', 'Northwest Region', 'Sarah Davis'),
            ('MOUNTAIN', 'Mountain Region', 'Michael Wilson'),
            ('CENTRAL', 'Central Region', 'Jennifer Miller')
        ]
        
        for region_code, region_name, manager in regions:
            established_date = fake.date_between(start_date='-30y', end_date='-5y')
            
            self.cursor.execute("""
                INSERT INTO regions (region_code, region_name, region_manager, established_date)
                VALUES (%s, %s, %s, %s) RETURNING region_id;
            """, (region_code, region_name, manager, established_date))
            self.region_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.region_ids)} regions")

    def generate_branches(self, count=150):
        """Generate bank branches"""
        print(f"🏦 Generating {count} branches...")
        
        branch_types = ['FULL_SERVICE', 'LIMITED_SERVICE', 'ATM_ONLY', 'COMMERCIAL', 'DRIVE_THRU']
        
        for i in range(count):
            region_id = random.choice(self.region_ids)
            city_id = random.choice(self.city_ids)
            branch_code = f"BR{i+1:04d}"
            branch_name = f"{fake.city()} Branch"
            
            self.cursor.execute("""
                INSERT INTO branches (
                    region_id, branch_code, branch_name, city_id,
                    address_line1, address_line2, zip_code, phone,
                    manager_name, opened_date, branch_type,
                    square_footage, employee_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING branch_id;
            """, (
                region_id, branch_code, branch_name, city_id,
                fake.street_address(), fake.secondary_address() if random.random() < 0.3 else None,
                fake.postcode(), fake.phone_number()[:15],
                fake.name(), fake.date_between(start_date='-20y', end_date='-1y'),
                random.choice(branch_types),
                random.randint(2000, 15000), random.randint(5, 50)
            ))
            self.branch_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.branch_ids)} branches")

    def generate_departments(self):
        """Generate bank departments"""
        print("🏢 Generating departments...")
        
        departments = [
            ('RETAIL', 'Retail Banking', 'Consumer banking services'),
            ('COMMERCIAL', 'Commercial Banking', 'Business banking services'),
            ('WEALTH', 'Wealth Management', 'Investment and wealth services'),
            ('LENDING', 'Lending Services', 'Loan and credit services'),
            ('OPERATIONS', 'Operations', 'Back office operations'),
            ('COMPLIANCE', 'Compliance', 'Regulatory compliance'),
            ('IT', 'Information Technology', 'Technology services'),
            ('HR', 'Human Resources', 'Employee services'),
            ('MARKETING', 'Marketing', 'Marketing and communications'),
            ('FINANCE', 'Finance', 'Financial planning and analysis')
        ]
        
        for dept_code, dept_name, description in departments:
            self.cursor.execute("""
                INSERT INTO departments (department_code, department_name, description)
                VALUES (%s, %s, %s) RETURNING department_id;
            """, (dept_code, dept_name, description))
            self.department_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.department_ids)} departments")

    def generate_employees(self, count=800):
        """Generate bank employees"""
        print(f"👥 Generating {count} employees...")
        
        job_titles = [
            'Branch Manager', 'Assistant Manager', 'Personal Banker', 'Teller',
            'Loan Officer', 'Customer Service Representative', 'Financial Advisor',
            'Compliance Officer', 'Operations Specialist', 'IT Specialist',
            'Marketing Coordinator', 'HR Generalist', 'Accountant', 'Auditor'
        ]
        
        for i in range(count):
            branch_id = random.choice(self.branch_ids)
            department_id = random.choice(self.department_ids)
            employee_number = f"EMP{i+1:06d}"

            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()

            hire_date = fake.date_between(start_date='-10y', end_date='today')
            salary = random.randint(35000, 150000)
            commission_rate = random.uniform(0.0000, 0.0500) if random.random() < 0.3 else 0.0000
            
            self.cursor.execute("""
                INSERT INTO employees (
                    branch_id, department_id, employee_number, first_name, last_name,
                    email, phone, hire_date, job_title, salary, commission_rate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING employee_id;
            """, (
                branch_id, department_id, employee_number, first_name, last_name,
                email, fake.phone_number()[:15], hire_date,
                random.choice(job_titles), salary, commission_rate
            ))
            self.employee_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        
        # Assign managers (some employees report to other employees)
        print("👨‍💼 Assigning managers...")
        for _ in range(min(200, len(self.employee_ids) // 4)):
            employee_id = random.choice(self.employee_ids)
            manager_id = random.choice(self.employee_ids)
            
            if employee_id != manager_id:
                self.cursor.execute("""
                    UPDATE employees SET manager_id = %s WHERE employee_id = %s;
                """, (manager_id, employee_id))
        
        self.conn.commit()
        print(f"✅ Created {len(self.employee_ids)} employees with management hierarchy")

    def generate_customer_segments(self):
        """Generate customer segments"""
        print("💎 Generating customer segments...")
        
        segments = [
            ('BASIC', 'Basic Banking', 0, 10000, 'Basic banking services', 0),
            ('PREFERRED', 'Preferred Customer', 10000, 50000, 'Enhanced services and lower fees', 50),
            ('PREMIUM', 'Premium Banking', 50000, 250000, 'Premium services and dedicated support', 150),
            ('PRIVATE', 'Private Banking', 250000, 1000000, 'Private banking and wealth management', 500),
            ('ELITE', 'Elite Banking', 1000000, None, 'Exclusive elite services', 1000)
        ]
        
        for code, name, min_val, max_val, benefits, fee in segments:
            self.cursor.execute("""
                INSERT INTO customer_segments (
                    segment_code, segment_name, min_relationship_value,
                    max_relationship_value, benefits_description, annual_fee
                ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING segment_id;
            """, (code, name, min_val, max_val, benefits, fee))
            self.customer_segment_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.customer_segment_ids)} customer segments")

    def generate_customer_types(self):
        """Generate customer types"""
        print("👤 Generating customer types...")
        
        types = [
            ('INDIVIDUAL', 'Individual Customer', 'Personal banking customer', False, False, 18),
            ('BUSINESS', 'Business Customer', 'Small business customer', True, True, 18),
            ('CORPORATE', 'Corporate Customer', 'Large corporate customer', True, True, 21),
            ('NON_PROFIT', 'Non-Profit Organization', 'Non-profit organization', True, True, 18),
            ('TRUST', 'Trust Account', 'Trust and estate account', False, False, 18)
        ]
        
        for code, name, desc, license_req, ein_req, min_age in types:
            self.cursor.execute("""
                INSERT INTO customer_types (
                    type_code, type_name, description, requires_business_license,
                    requires_ein, minimum_age
                ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING customer_type_id;
            """, (code, name, desc, license_req, ein_req, min_age))
            self.customer_type_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.customer_type_ids)} customer types")

    def generate_customers(self, count=5000):
        """Generate customers with realistic profiles"""
        print(f"👥 Generating {count} customers...")
        
        employment_statuses = ['EMPLOYED', 'SELF_EMPLOYED', 'UNEMPLOYED', 'RETIRED', 'STUDENT', 'HOMEMAKER']
        risk_ratings = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        kyc_statuses = ['PENDING', 'VERIFIED', 'EXPIRED', 'REJECTED']
        aml_statuses = ['CLEAR', 'REVIEW', 'SUSPICIOUS', 'BLOCKED']
        
        for i in tqdm(range(count), desc="Creating customers"):
            customer_number = f"CUST{i+1:08d}"
            customer_type_id = random.choice(self.customer_type_ids)
            segment_id = random.choice(self.customer_segment_ids)
            relationship_manager_id = random.choice(self.employee_ids) if random.random() < 0.7 else None
            primary_branch_id = random.choice(self.branch_ids)

            first_name = fake.first_name()[:50]  # Truncate to 50 chars
            last_name = fake.last_name()[:50]   # Truncate to 50 chars
            email = fake.unique.email()
            
            # Generate realistic financial profile
            annual_income = random.randint(25000, 500000)
            credit_score = random.randint(300, 850)
            total_relationship_value = random.randint(1000, 1000000)
            
            customer_since = fake.date_between(start_date='-20y', end_date='today')
            
            self.cursor.execute("""
                INSERT INTO customers (
                    customer_number, customer_type_id, segment_id, relationship_manager_id,
                    primary_branch_id, first_name, last_name, email, phone_primary,
                    address_line1, city_id, zip_code, date_of_birth, ssn,
                    annual_income, employment_status, employer_name, occupation,
                    credit_score, customer_since, risk_rating, kyc_status, aml_status,
                    total_relationship_value, lifetime_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING customer_id;
            """, (
                customer_number, customer_type_id, segment_id, relationship_manager_id,
                primary_branch_id, first_name, last_name, email, fake.phone_number()[:15],
                fake.street_address(), random.choice(self.city_ids), fake.postcode(),
                fake.date_of_birth(minimum_age=18, maximum_age=90), fake.ssn(),
                annual_income, random.choice(employment_statuses), fake.company()[:100],
                fake.job()[:50], credit_score, customer_since,
                random.choice(risk_ratings), random.choice(kyc_statuses), random.choice(aml_statuses),
                total_relationship_value, total_relationship_value * random.uniform(1.1, 1.5)
            ))
            self.customer_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.customer_ids)} customers")

    def generate_product_categories(self):
        """Generate product categories"""
        print("📦 Generating product categories...")
        
        categories = [
            ('CHECKING', 'Checking Accounts', 'DEPOSIT', 'Demand deposit accounts'),
            ('SAVINGS', 'Savings Accounts', 'DEPOSIT', 'Savings and money market accounts'),
            ('CD', 'Certificates of Deposit', 'DEPOSIT', 'Time deposit accounts'),
            ('MORTGAGE', 'Mortgage Loans', 'LOAN', 'Residential mortgage products'),
            ('AUTO', 'Auto Loans', 'LOAN', 'Vehicle financing'),
            ('PERSONAL', 'Personal Loans', 'LOAN', 'Unsecured personal loans'),
            ('CREDIT', 'Credit Cards', 'CARD', 'Credit card products'),
            ('DEBIT', 'Debit Cards', 'CARD', 'Debit card products'),
            ('INVESTMENT', 'Investment Products', 'INVESTMENT', 'Investment and brokerage'),
            ('INSURANCE', 'Insurance Products', 'INSURANCE', 'Banking insurance products')
        ]
        
        for code, name, type_cat, desc in categories:
            self.cursor.execute("""
                INSERT INTO product_categories (category_code, category_name, category_type, description)
                VALUES (%s, %s, %s, %s) RETURNING category_id;
            """, (code, name, type_cat, desc))
            self.product_category_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.product_category_ids)} product categories")

    def generate_products(self, count=50):
        """Generate banking products"""
        print(f"💳 Generating {count} products...")
        
        product_templates = [
            # Checking accounts
            ('BASIC_CHK', 'Basic Checking', 0, None, 0.0100, 0.0000, 5.00, 0, 0),
            ('PREMIUM_CHK', 'Premium Checking', 2500, None, 0.0150, 0.0000, 0, 0, 500),
            ('STUDENT_CHK', 'Student Checking', 0, None, 0.0050, 0.0000, 0, 0, 0),
            
            # Savings accounts  
            ('BASIC_SAV', 'Basic Savings', 100, None, 0.0200, 0.0000, 0, 0, 0),
            ('HIGH_YIELD_SAV', 'High Yield Savings', 10000, None, 0.0450, 0.0000, 0, 0, 0),
            ('MONEY_MARKET', 'Money Market Account', 2500, None, 0.0350, 0.0000, 0, 0, 0),
            
            # CDs
            ('CD_12M', '12 Month CD', 1000, None, 0.0400, 0.0100, 0, 0, 0),
            ('CD_24M', '24 Month CD', 1000, None, 0.0450, 0.0100, 0, 0, 0),
            ('CD_60M', '60 Month CD', 1000, None, 0.0500, 0.0100, 0, 0, 0)
        ]
        
        products_created = 0
        for code, name, min_bal, max_bal, interest, penalty, monthly, annual, overdraft in product_templates:
            if products_created >= count:
                break
                
            # Find appropriate category
            if 'CHK' in code:
                category_id = next(id for id in self.product_category_ids if self.get_category_code(id) == 'CHECKING')
            elif 'SAV' in code or 'MONEY' in code:
                category_id = next(id for id in self.product_category_ids if self.get_category_code(id) == 'SAVINGS')
            elif 'CD' in code:
                category_id = next(id for id in self.product_category_ids if self.get_category_code(id) == 'CD')
            else:
                category_id = random.choice(self.product_category_ids)
            
            self.cursor.execute("""
                INSERT INTO products (
                    category_id, product_code, product_name, minimum_balance,
                    maximum_balance, base_interest_rate, penalty_rate,
                    monthly_fee, annual_fee, overdraft_limit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING product_id;
            """, (category_id, code, name, min_bal, max_bal, interest, penalty, monthly, annual, overdraft))
            self.product_ids.append(self.cursor.fetchone()[0])
            products_created += 1
        
        # Generate additional random products
        for i in range(count - products_created):
            category_id = random.choice(self.product_category_ids)
            product_code = f"PROD{i+100:03d}"
            product_name = f"{fake.company()[:100]} Product"

            self.cursor.execute("""
                INSERT INTO products (
                    category_id, product_code, product_name, minimum_balance,
                    base_interest_rate, monthly_fee, annual_fee
                ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING product_id;
            """, (
                category_id, product_code, product_name,
                random.randint(0, 5000), random.uniform(0.0000, 0.0500),
                random.randint(0, 25), random.randint(0, 100)
            ))
            self.product_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.product_ids)} products")

    def get_category_code(self, category_id):
        """Helper to get category code by ID"""
        self.cursor.execute("SELECT category_code FROM product_categories WHERE category_id = %s", (category_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def generate_accounts(self, count=8000):
        """Generate customer accounts"""
        print(f"💰 Generating {count} accounts...")
        
        for i in tqdm(range(count), desc="Creating accounts"):
            customer_id = random.choice(self.customer_ids)
            product_id = random.choice(self.product_ids)
            branch_id = random.choice(self.branch_ids)
            relationship_manager_id = random.choice(self.employee_ids) if random.random() < 0.6 else None
            
            account_number = f"{random.randint(100000000, 999999999)}"
            current_balance = random.uniform(100, 100000)
            available_balance = current_balance * random.uniform(0.8, 1.0)
            
            opened_date = fake.date_between(start_date='-10y', end_date='today')
            
            self.cursor.execute("""
                INSERT INTO accounts (
                    customer_id, product_id, branch_id, relationship_manager_id,
                    account_number, current_balance, available_balance,
                    pending_balance, minimum_balance, interest_rate,
                    opened_date, daily_transaction_limit, monthly_transaction_limit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING account_id;
            """, (
                customer_id, product_id, branch_id, relationship_manager_id,
                account_number, current_balance, available_balance,
                random.uniform(0, 1000), random.uniform(0, 2500),
                random.uniform(0.0000, 0.0500), opened_date,
                random.randint(1000, 10000), random.randint(50000, 200000)
            ))
            self.account_ids.append(self.cursor.fetchone()[0])
        
        self.conn.commit()
        print(f"✅ Created {len(self.account_ids)} accounts")

    def generate_transaction_types(self):
        """Generate transaction types"""
        print("📝 Generating transaction types...")
        
        types = [
            ('DEPOSIT', 'Deposit', 'Cash or check deposit', 'CREDIT', False, False, False),
            ('WITHDRAWAL', 'Withdrawal', 'Cash withdrawal', 'DEBIT', False, True, False),
            ('XFER_IN', 'Transfer In', 'Incoming transfer', 'CREDIT', False, False, False),
            ('XFER_OUT', 'Transfer Out', 'Outgoing transfer', 'DEBIT', False, True, False),
            ('FEE', 'Fee', 'Bank fee charge', 'DEBIT', False, False, True),
            ('INTEREST', 'Interest', 'Interest payment', 'CREDIT', False, False, True),
            ('PURCHASE', 'Purchase', 'Debit card purchase', 'DEBIT', False, False, False),
            ('ATM', 'ATM Transaction', 'ATM withdrawal or deposit', 'BOTH', False, True, False),
            ('CHECK', 'Check Payment', 'Check clearing', 'DEBIT', False, False, False),
            ('ACH_DB', 'ACH Debit', 'Automated clearing house debit', 'DEBIT', False, False, True),
            ('ACH_CR', 'ACH Credit', 'Automated clearing house credit', 'CREDIT', False, False, True),
            ('WIRE_IN', 'Wire Transfer In', 'Incoming wire transfer', 'CREDIT', True, True, True),
            ('WIRE_OUT', 'Wire Transfer Out', 'Outgoing wire transfer', 'DEBIT', True, True, True),
            ('OVERDRAFT', 'Overdraft Fee', 'Overdraft penalty', 'DEBIT', False, False, True),
            ('REFUND', 'Refund', 'Transaction refund', 'CREDIT', False, False, False)
       ]
       
        for code, name, desc, debit_credit, approval, fee, reporting in types:
           self.cursor.execute("""
               INSERT INTO transaction_types (
                   type_code, type_name, description, debit_credit,
                   requires_approval, fee_applicable, regulatory_reporting
               ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING transaction_type_id;
           """, (code, name, desc, debit_credit, approval, fee, reporting))
           self.transaction_type_ids.append(self.cursor.fetchone()[0])

        self.conn.commit()
        print(f"✅ Created {len(self.transaction_type_ids)} transaction types")

    def generate_merchant_categories(self):
       """Generate merchant category codes (MCC)"""
       print("🏪 Generating merchant categories...")
       
       mccs = [
           ('5411', 'Grocery Stores', 'Supermarkets and grocery stores', 'LOW'),
           ('5541', 'Service Stations', 'Gas stations and fuel', 'LOW'),
           ('5812', 'Eating Places', 'Restaurants and dining', 'LOW'),
           ('5311', 'Department Stores', 'General merchandise stores', 'LOW'),
           ('5691', 'Mens and Womens Clothing', 'Apparel and clothing', 'LOW'),
           ('5732', 'Electronics Stores', 'Consumer electronics', 'MEDIUM'),
           ('5999', 'Miscellaneous Retail', 'Other retail establishments', 'MEDIUM'),
           ('6011', 'Financial Institutions', 'Banks and credit unions', 'HIGH'),
           ('7011', 'Hotels and Motels', 'Lodging establishments', 'MEDIUM'),
           ('7841', 'Video Entertainment', 'Movie theaters and entertainment', 'LOW'),
           ('4111', 'Transportation', 'Local and suburban transit', 'LOW'),
           ('5967', 'Direct Marketing', 'Mail order and online retail', 'MEDIUM'),
           ('5993', 'Cigar Stores', 'Tobacco products', 'HIGH'),
           ('7995', 'Gambling', 'Betting and gambling', 'HIGH'),
           ('6051', 'Quasi Cash', 'Money orders and traveler checks', 'HIGH')
       ]
       
       for code, name, desc, risk in mccs:
           self.cursor.execute("""
               INSERT INTO merchant_categories (mcc_code, category_name, category_description, risk_level)
               VALUES (%s, %s, %s, %s) RETURNING mcc_id;
           """, (code, name, desc, risk))
           self.mcc_ids.append(self.cursor.fetchone()[0])
       
       self.conn.commit()
       print(f"✅ Created {len(self.mcc_ids)} merchant categories")

    def generate_merchants(self, count=1000):
       """Generate merchants"""
       print(f"🏢 Generating {count} merchants...")
       
       for i in tqdm(range(count), desc="Creating merchants"):
           mcc_id = random.choice(self.mcc_ids)
           merchant_name = fake.company()[:100],  # employer_name
           dba_name = merchant_name if random.random() < 0.7 else fake.company()[:100]
           merchant_number = f"MERCH{i+1:06d}"
           city_id = random.choice(self.city_ids)
           
           self.cursor.execute("""
               INSERT INTO merchants (
                   mcc_id, merchant_name, dba_name, merchant_number,
                   city_id, address_line1, zip_code, phone
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING merchant_id;
           """, (
               mcc_id, merchant_name, dba_name, merchant_number,
               city_id, fake.street_address(), fake.postcode(), fake.phone_number()[:15]
           ))
           self.merchant_ids.append(self.cursor.fetchone()[0])
       
       self.conn.commit()
       print(f"✅ Created {len(self.merchant_ids)} merchants")

    def generate_transactions(self, count=50000):
       """Generate realistic banking transactions"""
       print(f"💳 Generating {count} transactions...")
       
       channels = ['ATM', 'ONLINE', 'MOBILE', 'BRANCH', 'PHONE', 'ACH', 'WIRE', 'CHECK', 'CARD']
       statuses = ['PENDING', 'POSTED', 'DECLINED', 'REVERSED', 'CANCELLED']
       
       for i in tqdm(range(count), desc="Creating transactions"):
           account_id = random.choice(self.account_ids)
           transaction_type_id = random.choice(self.transaction_type_ids)
           merchant_id = random.choice(self.merchant_ids) if random.random() < 0.7 else None
           
           transaction_number = f"TXN{i+1:010d}"
           transaction_amount = round(random.uniform(-5000, 5000), 2)
           fee_amount = round(random.uniform(0, 25), 2) if random.random() < 0.2 else 0
           total_amount = transaction_amount + fee_amount
           
           transaction_date = fake.date_time_between(start_date='-2y', end_date='now')
           
           # Generate realistic running balance
           running_balance = round(random.uniform(100, 50000), 2)
           
           self.cursor.execute("""
               INSERT INTO transactions (
                   account_id, transaction_type_id, merchant_id, transaction_number,
                   reference_number, authorization_code, transaction_amount,
                   fee_amount, total_amount, running_balance, original_amount,
                   original_currency, exchange_rate, transaction_date,
                   value_date, posted_date, description, memo, category,
                   channel, terminal_id, location_description, city_id,
                   status, risk_score, fraud_flag, aml_flag, batch_id
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING transaction_id;
           """, (
               account_id, transaction_type_id, merchant_id, transaction_number,
               f"REF{random.randint(100000, 999999)}", f"AUTH{random.randint(100000, 999999)}",
               transaction_amount, fee_amount, total_amount, running_balance,
               abs(transaction_amount), 'USD', 1.000000, transaction_date,
               transaction_date.date(), transaction_date + timedelta(hours=random.randint(1, 48)),
               fake.sentence(nb_words=6), fake.text(max_nb_chars=50),
               random.choice(['GROCERIES', 'GAS', 'DINING', 'SHOPPING', 'BILLS', 'ENTERTAINMENT']),
               random.choice(channels), f"TERM{random.randint(1000, 9999)}",
               fake.street_address(), random.choice(self.city_ids),
               random.choice(statuses), random.randint(0, 100),
               random.random() < 0.01, random.random() < 0.005,
               f"BATCH{random.randint(1000, 9999)}"
           ))
       
       self.conn.commit()
       print(f"✅ Created {count} transactions")

    def generate_summary_stats(self):
       """Generate and display summary statistics"""
       print("\n📊 Database Summary Statistics")
       print("=" * 50)
       
       tables = [
           'countries', 'states', 'cities', 'regions', 'branches', 'departments',
           'employees', 'customer_segments', 'customer_types', 'customers',
           'product_categories', 'products', 'accounts', 'transaction_types',
           'merchant_categories', 'merchants', 'transactions'
       ]
       
       for table in tables:
           self.cursor.execute(f"SELECT COUNT(*) FROM {table};")
           count = self.cursor.fetchone()[0]
           print(f"📋 {table.replace('_', ' ').title()}: {count:,} records")
       
       # Additional analytics
       self.cursor.execute("""
           SELECT 
               SUM(current_balance) as total_deposits,
               AVG(current_balance) as avg_balance,
               COUNT(*) as total_accounts
           FROM accounts;
       """)
       deposits, avg_balance, total_accounts = self.cursor.fetchone()
       print(f"\n💰 Total Deposits: ${deposits:,.2f}")
       print(f"📈 Average Account Balance: ${avg_balance:,.2f}")
       print(f"🏦 Total Accounts: {total_accounts:,}")
       
       self.cursor.execute("""
           SELECT 
               SUM(transaction_amount) as total_transaction_volume,
               COUNT(*) as total_transactions
           FROM transactions 
           WHERE status = 'POSTED';
       """)
       volume, txn_count = self.cursor.fetchone()
       print(f"💳 Total Transaction Volume: ${volume:,.2f}")
       print(f"📊 Total Posted Transactions: {txn_count:,}")

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive banking data')
    parser.add_argument('--customers', type=int, default=5000, help='Number of customers to generate')
    parser.add_argument('--accounts', type=int, default=8000, help='Number of accounts to generate')
    parser.add_argument('--transactions', type=int, default=50000, help='Number of transactions to generate')
    parser.add_argument('--employees', type=int, default=800, help='Number of employees to generate')
    parser.add_argument('--merchants', type=int, default=1000, help='Number of merchants to generate')
    parser.add_argument('--db-name', default='banking_rag_db', help='Database name')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', default='5432', help='Database port')
    parser.add_argument('--user', default='nba', help='Database user')

    args = parser.parse_args()

    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
           host=args.host,
           port=args.port,
           database=args.db_name,
           user=args.user
        )
        print(f"✅ Connected to PostgreSQL database: {args.db_name}")

        # Generate all data
        generator = BankingDataGenerator(conn)

        print("\n🚀 Starting comprehensive banking data generation...")
        print("=" * 60)

        # Generate reference data first (required for foreign keys)
        generator.generate_countries()
        generator.generate_states()
        generator.generate_cities()
        generator.generate_regions()
        generator.generate_branches()
        generator.generate_departments()
        generator.generate_employees(args.employees)

        # Generate customer framework
        generator.generate_customer_segments()
        generator.generate_customer_types()
        generator.generate_customers(args.customers)

        # Generate products and accounts
        generator.generate_product_categories()
        generator.generate_products()
        generator.generate_accounts(args.accounts)

        # Generate transaction framework
        generator.generate_transaction_types()
        generator.generate_merchant_categories()
        generator.generate_merchants(args.merchants)
        generator.generate_transactions(args.transactions)

        # Generate summary
        generator.generate_summary_stats()

        conn.close()
        print(f"\n🎉 Data generation completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
EOF           
