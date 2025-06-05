-- Enhanced Banking Schema with Comprehensive Constraints
-- Compatible with PostgreSQL 17, MySQL 9, Oracle 21c, SQL Server 2022

-- Reference/Lookup Tables with Constraints
CREATE TABLE countries (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR(3) NOT NULL UNIQUE CHECK (LENGTH(country_code) = 3 AND country_code = UPPER(country_code)),
    country_name VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(country_name)) > 0),
    currency_code VARCHAR(3) NOT NULL CHECK (LENGTH(currency_code) = 3 AND currency_code = UPPER(currency_code)),
    tax_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (tax_rate >= 0.0000 AND tax_rate <= 1.0000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_countries_name UNIQUE (country_name)
);

CREATE TABLE states (
    state_id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(country_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    state_code VARCHAR(5) NOT NULL CHECK (LENGTH(TRIM(state_code)) BETWEEN 2 AND 5),
    state_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(state_name)) > 0),
    tax_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (tax_rate >= 0.0000 AND tax_rate <= 1.0000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_states_code_country UNIQUE (country_id, state_code),
    CONSTRAINT uk_states_name_country UNIQUE (country_id, state_name)
);

CREATE TABLE cities (
    city_id SERIAL PRIMARY KEY,
    state_id INTEGER NOT NULL REFERENCES states(state_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    city_name VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(city_name)) > 0),
    population INTEGER CHECK (population > 0 AND population <= 50000000),
    median_income DECIMAL(12,2) CHECK (median_income >= 0),
    zip_code_primary VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_cities_name_state UNIQUE (state_id, city_name)
);

-- Bank Infrastructure
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(region_name)) > 0),
    region_code VARCHAR(10) NOT NULL UNIQUE CHECK (LENGTH(TRIM(region_code)) BETWEEN 2 AND 10),
    region_manager VARCHAR(100) CHECK (LENGTH(TRIM(region_manager)) > 0),
    established_date DATE CHECK (established_date >= '1800-01-01' AND established_date <= CURRENT_DATE),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES regions(region_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    branch_code VARCHAR(10) NOT NULL UNIQUE CHECK (LENGTH(TRIM(branch_code)) BETWEEN 3 AND 10),
    branch_name VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(branch_name)) > 0),
    city_id INTEGER NOT NULL REFERENCES cities(city_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    address_line1 VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(address_line1)) > 0),
    address_line2 VARCHAR(100),
    zip_code VARCHAR(10) NOT NULL CHECK (LENGTH(TRIM(zip_code)) BETWEEN 5 AND 10),
    phone VARCHAR(15) CHECK (LENGTH(TRIM(phone)) >= 10),
    manager_name VARCHAR(100) CHECK (LENGTH(TRIM(manager_name)) > 0),
    opened_date DATE DEFAULT CURRENT_DATE CHECK (opened_date >= '1800-01-01' AND opened_date <= CURRENT_DATE),
    closed_date DATE CHECK (closed_date IS NULL OR closed_date >= opened_date),
    branch_type VARCHAR(20) NOT NULL DEFAULT 'FULL_SERVICE' 
        CHECK (branch_type IN ('FULL_SERVICE', 'LIMITED_SERVICE', 'ATM_ONLY', 'COMMERCIAL', 'DRIVE_THRU')),
    square_footage INTEGER CHECK (square_footage > 0 AND square_footage <= 100000),
    employee_count INTEGER DEFAULT 0 CHECK (employee_count >= 0 AND employee_count <= 500),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(department_name)) > 0),
    department_code VARCHAR(10) NOT NULL UNIQUE CHECK (LENGTH(TRIM(department_code)) BETWEEN 2 AND 10),
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    employee_number VARCHAR(20) NOT NULL UNIQUE CHECK (LENGTH(TRIM(employee_number)) BETWEEN 5 AND 20),
    first_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(first_name)) > 0),
    last_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(last_name)) > 0),
    middle_name VARCHAR(50),
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) CHECK (LENGTH(TRIM(phone)) >= 10),
    hire_date DATE DEFAULT CURRENT_DATE CHECK (hire_date >= '1900-01-01' AND hire_date <= CURRENT_DATE + INTERVAL '30 days'),
    termination_date DATE CHECK (termination_date IS NULL OR termination_date >= hire_date),
    job_title VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(job_title)) > 0),
    salary DECIMAL(12,2) CHECK (salary >= 0 AND salary <= 10000000),
    commission_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (commission_rate >= 0.0000 AND commission_rate <= 1.0000),
    manager_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL ON UPDATE CASCADE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_employee_not_self_manager CHECK (employee_id != manager_id)
);

-- Customer Hierarchy
CREATE TABLE customer_segments (
    segment_id SERIAL PRIMARY KEY,
    segment_name VARCHAR(50) NOT NULL UNIQUE CHECK (LENGTH(TRIM(segment_name)) > 0),
    segment_code VARCHAR(10) NOT NULL UNIQUE CHECK (LENGTH(TRIM(segment_code)) BETWEEN 2 AND 10),
    min_relationship_value DECIMAL(15,2) DEFAULT 0.00 CHECK (min_relationship_value >= 0),
    max_relationship_value DECIMAL(15,2) CHECK (max_relationship_value IS NULL OR max_relationship_value >= min_relationship_value),
    benefits_description TEXT,
    annual_fee DECIMAL(8,2) DEFAULT 0.00 CHECK (annual_fee >= 0 AND annual_fee <= 100000),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_types (
    customer_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(30) NOT NULL UNIQUE CHECK (LENGTH(TRIM(type_name)) > 0),
    type_code VARCHAR(10) NOT NULL UNIQUE CHECK (LENGTH(TRIM(type_code)) BETWEEN 2 AND 10),
    description TEXT,
    requires_business_license BOOLEAN DEFAULT false NOT NULL,
    requires_ein BOOLEAN DEFAULT false NOT NULL,
    minimum_age INTEGER DEFAULT 18 CHECK (minimum_age >= 0 AND minimum_age <= 150),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_number VARCHAR(20) NOT NULL UNIQUE CHECK (LENGTH(TRIM(customer_number)) BETWEEN 8 AND 20),
    customer_type_id INTEGER NOT NULL REFERENCES customer_types(customer_type_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    segment_id INTEGER REFERENCES customer_segments(segment_id) ON DELETE SET NULL ON UPDATE CASCADE,
    relationship_manager_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL ON UPDATE CASCADE,
    primary_branch_id INTEGER REFERENCES branches(branch_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Personal Information
    first_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(first_name)) > 0),
    last_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(last_name)) > 0),
    middle_name VARCHAR(50),
    date_of_birth DATE CHECK (date_of_birth IS NULL OR (date_of_birth >= '1900-01-01' AND date_of_birth <= CURRENT_DATE - INTERVAL '13 years')),
    ssn VARCHAR(11) UNIQUE,
    ein VARCHAR(10),
    
    -- Contact Information
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_primary VARCHAR(15) CHECK (LENGTH(TRIM(phone_primary)) >= 10),
    phone_secondary VARCHAR(15),
    
    -- Address Information
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    city_id INTEGER REFERENCES cities(city_id) ON DELETE SET NULL ON UPDATE CASCADE,
    zip_code VARCHAR(10),
    
    -- Financial Profile
    annual_income DECIMAL(15,2) CHECK (annual_income IS NULL OR (annual_income >= 0 AND annual_income <= 100000000)),
    employment_status VARCHAR(30) CHECK (employment_status IS NULL OR employment_status IN 
        ('EMPLOYED', 'SELF_EMPLOYED', 'UNEMPLOYED', 'RETIRED', 'STUDENT', 'HOMEMAKER', 'DISABLED')),
    employer_name VARCHAR(100),
    occupation VARCHAR(50),
    credit_score INTEGER CHECK (credit_score IS NULL OR (credit_score BETWEEN 300 AND 850)),
    
    -- Customer Lifecycle
    customer_since DATE DEFAULT CURRENT_DATE CHECK (customer_since >= '1900-01-01' AND customer_since <= CURRENT_DATE),
    last_contact_date DATE,
    next_review_date DATE,
    risk_rating VARCHAR(10) DEFAULT 'MEDIUM' CHECK (risk_rating IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    kyc_status VARCHAR(20) DEFAULT 'PENDING' CHECK (kyc_status IN ('PENDING', 'VERIFIED', 'EXPIRED', 'REJECTED')),
    aml_status VARCHAR(20) DEFAULT 'CLEAR' CHECK (aml_status IN ('CLEAR', 'REVIEW', 'SUSPICIOUS', 'BLOCKED')),
    
    -- Relationship Value
    total_relationship_value DECIMAL(15,2) DEFAULT 0.00 CHECK (total_relationship_value >= 0),
    lifetime_value DECIMAL(15,2) DEFAULT 0.00 CHECK (lifetime_value >= 0),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true NOT NULL
);

-- Product Hierarchy
CREATE TABLE product_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE CHECK (LENGTH(TRIM(category_name)) > 0),
    category_code VARCHAR(10) NOT NULL UNIQUE CHECK (LENGTH(TRIM(category_code)) BETWEEN 2 AND 10),
    category_type VARCHAR(30) NOT NULL CHECK (category_type IN ('DEPOSIT', 'LOAN', 'INVESTMENT', 'INSURANCE', 'SERVICE', 'CARD')),
    description TEXT,
    regulatory_code VARCHAR(20),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES product_categories(category_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    product_code VARCHAR(20) NOT NULL UNIQUE CHECK (LENGTH(TRIM(product_code)) BETWEEN 3 AND 20),
    product_name VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(product_name)) > 0),
    description TEXT,
    minimum_balance DECIMAL(15,2) DEFAULT 0.00 CHECK (minimum_balance >= 0),
    maximum_balance DECIMAL(15,2) CHECK (maximum_balance IS NULL OR maximum_balance >= minimum_balance),
    base_interest_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (base_interest_rate >= 0.0000 AND base_interest_rate <= 1.0000),
    penalty_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (penalty_rate >= 0.0000 AND penalty_rate <= 1.0000),
    monthly_fee DECIMAL(8,2) DEFAULT 0.00 CHECK (monthly_fee >= 0 AND monthly_fee <= 10000),
    annual_fee DECIMAL(8,2) DEFAULT 0.00 CHECK (annual_fee >= 0 AND annual_fee <= 100000),
    overdraft_limit DECIMAL(12,2) DEFAULT 0.00 CHECK (overdraft_limit >= 0),
    grace_period_days INTEGER DEFAULT 0 CHECK (grace_period_days >= 0 AND grace_period_days <= 90),
    is_active BOOLEAN DEFAULT true NOT NULL,
    launch_date DATE DEFAULT CURRENT_DATE CHECK (launch_date >= '1900-01-01'),
    discontinue_date DATE CHECK (discontinue_date IS NULL OR discontinue_date >= launch_date),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Account Management
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    relationship_manager_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    account_number VARCHAR(20) NOT NULL UNIQUE CHECK (LENGTH(TRIM(account_number)) BETWEEN 8 AND 20),
    routing_number VARCHAR(9) DEFAULT '021000021' CHECK (LENGTH(routing_number) = 9),
    iban VARCHAR(34),
    swift_code VARCHAR(11),
    
    -- Balances
    current_balance DECIMAL(15,2) DEFAULT 0.00,
    available_balance DECIMAL(15,2) DEFAULT 0.00,
    pending_balance DECIMAL(15,2) DEFAULT 0.00 CHECK (pending_balance >= 0),
    minimum_balance DECIMAL(15,2) DEFAULT 0.00 CHECK (minimum_balance >= 0),
    overdraft_limit DECIMAL(12,2) DEFAULT 0.00 CHECK (overdraft_limit >= 0),
    
    -- Rates and Fees
    interest_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (interest_rate >= 0.0000 AND interest_rate <= 1.0000),
    penalty_rate DECIMAL(5,4) DEFAULT 0.0000 CHECK (penalty_rate >= 0.0000 AND penalty_rate <= 1.0000),
    
    -- Account Lifecycle
    opened_date DATE DEFAULT CURRENT_DATE CHECK (opened_date >= '1900-01-01' AND opened_date <= CURRENT_DATE),
    closed_date DATE CHECK (closed_date IS NULL OR closed_date >= opened_date),
    maturity_date DATE CHECK (maturity_date IS NULL OR maturity_date > opened_date),
    last_transaction_date DATE,
    last_statement_date DATE,
    next_statement_date DATE,
    
    -- Status and Risk
    status VARCHAR(15) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED', 'SUSPENDED', 'FROZEN', 'DORMANT')),
    account_purpose VARCHAR(100),
    tax_reporting_required BOOLEAN DEFAULT false NOT NULL,
    regulatory_monitoring BOOLEAN DEFAULT false NOT NULL,
    daily_transaction_limit DECIMAL(12,2) DEFAULT 10000.00 CHECK (daily_transaction_limit >= 0),
    monthly_transaction_limit DECIMAL(15,2) DEFAULT 100000.00 CHECK (monthly_transaction_limit >= daily_transaction_limit),
    suspicious_activity_flag BOOLEAN DEFAULT false NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction Framework
CREATE TABLE transaction_types (
    transaction_type_id SERIAL PRIMARY KEY,
    type_code VARCHAR(10) UNIQUE NOT NULL CHECK (LENGTH(TRIM(type_code)) BETWEEN 2 AND 10),
    type_name VARCHAR(50) NOT NULL CHECK (LENGTH(TRIM(type_name)) > 0),
    description TEXT,
    debit_credit VARCHAR(6) CHECK (debit_credit IN ('DEBIT', 'CREDIT', 'BOTH')),
    requires_approval BOOLEAN DEFAULT false,
    fee_applicable BOOLEAN DEFAULT false,
    regulatory_reporting BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE merchant_categories (
    mcc_id SERIAL PRIMARY KEY,
    mcc_code VARCHAR(4) UNIQUE NOT NULL CHECK (LENGTH(mcc_code) = 4),
    category_name VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(category_name)) > 0),
    category_description TEXT,
    risk_level VARCHAR(10) DEFAULT 'LOW' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE merchants (
    merchant_id SERIAL PRIMARY KEY,
    mcc_id INTEGER NOT NULL REFERENCES merchant_categories(mcc_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    merchant_name VARCHAR(100) NOT NULL CHECK (LENGTH(TRIM(merchant_name)) > 0),
    dba_name VARCHAR(100),
    merchant_number VARCHAR(20) UNIQUE,
    city_id INTEGER REFERENCES cities(city_id) ON DELETE SET NULL ON UPDATE CASCADE,
    address_line1 VARCHAR(100),
    zip_code VARCHAR(10),
    phone VARCHAR(15),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Complex Transaction Table  
CREATE TABLE transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    transaction_type_id INTEGER NOT NULL REFERENCES transaction_types(transaction_type_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    merchant_id INTEGER REFERENCES merchants(merchant_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Transaction Identifiers
    transaction_number VARCHAR(30) UNIQUE NOT NULL,
    reference_number VARCHAR(50),
    authorization_code VARCHAR(20),
    
    -- Amounts
    transaction_amount DECIMAL(15,2) NOT NULL,
    fee_amount DECIMAL(8,2) DEFAULT 0.00 CHECK (fee_amount >= 0),
    total_amount DECIMAL(15,2) NOT NULL,
    running_balance DECIMAL(15,2),
    
    -- Currency
    original_amount DECIMAL(15,2),
    original_currency VARCHAR(3) DEFAULT 'USD',
    exchange_rate DECIMAL(10,6) DEFAULT 1.000000 CHECK (exchange_rate > 0),
    
    -- Timing
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value_date DATE,
    posted_date TIMESTAMP,
    effective_date DATE,
    
    -- Description
    description TEXT,
    memo VARCHAR(200),
    category VARCHAR(50),
    
    -- Channel and Location
    channel VARCHAR(20) CHECK (channel IN ('ATM', 'ONLINE', 'MOBILE', 'BRANCH', 'PHONE', 'ACH', 'WIRE', 'CHECK', 'CARD')),
    terminal_id VARCHAR(20),
    location_description VARCHAR(100),
    city_id INTEGER REFERENCES cities(city_id) ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Status and Risk
    status VARCHAR(15) DEFAULT 'POSTED' CHECK (status IN ('PENDING', 'POSTED', 'DECLINED', 'REVERSED', 'CANCELLED', 'DISPUTED')),
    hold_reason VARCHAR(100),
    release_date TIMESTAMP,
    risk_score INTEGER CHECK (risk_score IS NULL OR (risk_score BETWEEN 0 AND 100)),
    fraud_flag BOOLEAN DEFAULT false,
    aml_flag BOOLEAN DEFAULT false,
    regulatory_flag BOOLEAN DEFAULT false,
    
    -- Related Transactions
    parent_transaction_id BIGINT REFERENCES transactions(transaction_id) ON DELETE SET NULL ON UPDATE CASCADE,
    batch_id VARCHAR(30),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_ssn ON customers(ssn) WHERE ssn IS NOT NULL;
CREATE INDEX idx_customers_type_segment ON customers(customer_type_id, segment_id);
CREATE INDEX idx_customers_branch ON customers(primary_branch_id);
CREATE INDEX idx_customers_city ON customers(city_id);
CREATE INDEX idx_customers_status ON customers(is_active, kyc_status, aml_status);

CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_accounts_product ON accounts(product_id);
CREATE INDEX idx_accounts_branch ON accounts(branch_id);
CREATE INDEX idx_accounts_number ON accounts(account_number);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_opened_date ON accounts(opened_date);

CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type_id);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_amount ON transactions(transaction_amount);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_channel ON transactions(channel);

CREATE INDEX idx_employees_branch_dept ON employees(branch_id, department_id);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_employees_active ON employees(is_active);

CREATE INDEX idx_branches_region ON branches(region_id);
CREATE INDEX idx_branches_city ON branches(city_id);
CREATE INDEX idx_branches_active ON branches(is_active);

CREATE INDEX idx_merchants_mcc ON merchants(mcc_id);
CREATE INDEX idx_merchants_city ON merchants(city_id);
CREATE INDEX idx_merchants_active ON merchants(is_active);
