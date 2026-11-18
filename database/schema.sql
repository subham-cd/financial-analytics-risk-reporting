-- ============================================================================
-- FinSight Platform - Financial Intelligence & Credit Risk Reporting System
-- PostgreSQL Relational Database Schema
-- Evaluation Project: Nexvia Technologies
-- ============================================================================

-- Drop views if exist
DROP VIEW IF EXISTS view_monthly_pnl;
DROP VIEW IF EXISTS view_balance_sheet;
DROP VIEW IF EXISTS view_budget_vs_actual;
DROP VIEW IF EXISTS view_credit_risk_summary;

-- Drop tables with cascade
DROP TABLE IF EXISTS financial_reports CASCADE;
DROP TABLE IF EXISTS credit_predictions CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS borrowers CASCADE;
DROP TABLE IF EXISTS equity CASCADE;
DROP TABLE IF EXISTS liabilities CASCADE;
DROP TABLE IF EXISTS assets CASCADE;
DROP TABLE IF EXISTS expenses CASCADE;
DROP TABLE IF EXISTS revenue CASCADE;
DROP TABLE IF EXISTS budgets CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS chart_of_accounts CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- ----------------------------------------------------------------------------
-- 1. Departments Master Table
-- ----------------------------------------------------------------------------
CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    department_name VARCHAR(100) NOT NULL,
    cost_center VARCHAR(50) NOT NULL,
    manager_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Chart of Accounts Master Table
-- Follows GAAP standard accounting codes:
-- 1000s: Assets | 2000s: Liabilities | 3000s: Equity | 4000s: Revenue | 5000s: COGS | 6000s: Opex | 7000s: Tax & Other
-- ----------------------------------------------------------------------------
CREATE TABLE chart_of_accounts (
    account_id SERIAL PRIMARY KEY,
    account_code VARCHAR(20) NOT NULL UNIQUE,
    account_name VARCHAR(150) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    sub_category VARCHAR(100) NOT NULL,
    normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('Debit', 'Credit')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Financial Transactions Ledger
-- ----------------------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    transaction_date DATE NOT NULL,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL CHECK (fiscal_month BETWEEN 1 AND 12),
    fiscal_quarter INT NOT NULL CHECK (fiscal_quarter BETWEEN 1 AND 4),
    account_id INT NOT NULL REFERENCES chart_of_accounts(account_id) ON DELETE RESTRICT,
    department_id INT NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    transaction_category VARCHAR(50) NOT NULL CHECK (transaction_category IN ('Operating', 'Financing', 'Investing', 'Adjusting')),
    debit_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (debit_amount >= 0),
    credit_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (credit_amount >= 0),
    description TEXT,
    reference_no VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. Budgets Master Table
-- ----------------------------------------------------------------------------
CREATE TABLE budgets (
    budget_id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL CHECK (fiscal_month BETWEEN 1 AND 12),
    department_id INT NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    account_id INT NOT NULL REFERENCES chart_of_accounts(account_id) ON DELETE RESTRICT,
    budgeted_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (budgeted_amount >= 0),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dept_account_month UNIQUE(fiscal_year, fiscal_month, department_id, account_id)
);

-- ----------------------------------------------------------------------------
-- 5. Revenue Stream Records
-- ----------------------------------------------------------------------------
CREATE TABLE revenue (
    revenue_id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL,
    department_id INT NOT NULL REFERENCES departments(department_id),
    stream_type VARCHAR(100) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 6. Expense Records
-- ----------------------------------------------------------------------------
CREATE TABLE expenses (
    expense_id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL,
    department_id INT NOT NULL REFERENCES departments(department_id),
    expense_category VARCHAR(100) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 7. Assets Ledger
-- ----------------------------------------------------------------------------
CREATE TABLE assets (
    asset_id SERIAL PRIMARY KEY,
    asset_code VARCHAR(50) NOT NULL UNIQUE,
    asset_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL,
    book_value NUMERIC(15, 2) NOT NULL CHECK (book_value >= 0),
    accumulated_depreciation NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    net_value NUMERIC(15, 2) GENERATED ALWAYS AS (book_value - accumulated_depreciation) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 8. Liabilities Ledger
-- ----------------------------------------------------------------------------
CREATE TABLE liabilities (
    liability_id SERIAL PRIMARY KEY,
    liability_code VARCHAR(50) NOT NULL UNIQUE,
    liability_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL,
    current_balance NUMERIC(15, 2) NOT NULL CHECK (current_balance >= 0),
    interest_rate NUMERIC(5, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 9. Equity Ledger
-- ----------------------------------------------------------------------------
CREATE TABLE equity (
    equity_id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,
    fiscal_month INT NOT NULL,
    share_capital NUMERIC(15, 2) NOT NULL CHECK (share_capital >= 0),
    retained_earnings NUMERIC(15, 2) NOT NULL,
    total_equity NUMERIC(15, 2) GENERATED ALWAYS AS (share_capital + retained_earnings) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_equity_month UNIQUE(fiscal_year, fiscal_month)
);

-- ----------------------------------------------------------------------------
-- 10. Borrowers Master Table (Credit Risk Module)
-- ----------------------------------------------------------------------------
CREATE TABLE borrowers (
    borrower_id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    annual_income NUMERIC(15, 2) NOT NULL CHECK (annual_income > 0),
    employment_length_years NUMERIC(4, 1) NOT NULL DEFAULT 0.0,
    home_ownership VARCHAR(20) NOT NULL CHECK (home_ownership IN ('RENT', 'OWN', 'MORTGAGE', 'OTHER')),
    state_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 11. Loans Ledger
-- ----------------------------------------------------------------------------
CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    borrower_id INT NOT NULL REFERENCES borrowers(borrower_id) ON DELETE CASCADE,
    loan_amount NUMERIC(12, 2) NOT NULL CHECK (loan_amount > 0),
    loan_term_months INT NOT NULL CHECK (loan_term_months IN (36, 60)),
    interest_rate NUMERIC(6, 3) NOT NULL CHECK (interest_rate > 0),
    installment_amount NUMERIC(12, 2) NOT NULL,
    loan_grade VARCHAR(5) NOT NULL CHECK (loan_grade IN ('A', 'B', 'C', 'D', 'E', 'F', 'G')),
    debt_to_income_ratio NUMERIC(6, 2) NOT NULL,
    revolving_utilization_pct NUMERIC(6, 2) NOT NULL,
    total_credit_accounts INT NOT NULL DEFAULT 0,
    open_credit_accounts INT NOT NULL DEFAULT 0,
    derogatory_records INT NOT NULL DEFAULT 0,
    loan_purpose VARCHAR(50) NOT NULL,
    loan_status VARCHAR(50) NOT NULL CHECK (loan_status IN ('Fully Paid', 'Charged Off', 'Current', 'Default')),
    is_default INT NOT NULL CHECK (is_default IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 12. Credit Risk Predictions and Scorecards
-- ----------------------------------------------------------------------------
CREATE TABLE credit_predictions (
    prediction_id SERIAL PRIMARY KEY,
    loan_id INT REFERENCES loans(loan_id) ON DELETE CASCADE,
    borrower_id INT NOT NULL REFERENCES borrowers(borrower_id) ON DELETE CASCADE,
    predicted_prob_default NUMERIC(6, 4) NOT NULL CHECK (predicted_prob_default BETWEEN 0 AND 1),
    credit_score INT NOT NULL CHECK (credit_score BETWEEN 300 AND 850),
    risk_band VARCHAR(20) NOT NULL CHECK (risk_band IN ('Low Risk', 'Medium Risk', 'High Risk', 'Very High Risk')),
    woe_score NUMERIC(10, 4),
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0-logistic-woe',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 13. Financial Reports Catalog
-- ----------------------------------------------------------------------------
CREATE TABLE financial_reports (
    report_id SERIAL PRIMARY KEY,
    report_name VARCHAR(150) NOT NULL,
    report_period VARCHAR(20) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size_bytes INT,
    generated_by VARCHAR(100) DEFAULT 'FinSight-Engine',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- INDEXES for Query Optimization
-- ----------------------------------------------------------------------------
CREATE INDEX idx_transactions_period ON transactions(fiscal_year, fiscal_month);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_department ON transactions(department_id);
CREATE INDEX idx_budgets_period ON budgets(fiscal_year, fiscal_month);
CREATE INDEX idx_loans_borrower ON loans(borrower_id);
CREATE INDEX idx_loans_status ON loans(loan_status);
CREATE INDEX idx_loans_grade ON loans(loan_grade);
CREATE INDEX idx_predictions_score ON credit_predictions(credit_score);
CREATE INDEX idx_predictions_risk ON credit_predictions(risk_band);

-- ----------------------------------------------------------------------------
-- VIEWS: Financial Statement & Performance Views
-- ----------------------------------------------------------------------------

-- Monthly Profit and Loss View
CREATE OR REPLACE VIEW view_monthly_pnl AS
SELECT 
    t.fiscal_year,
    t.fiscal_month,
    SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END) AS cogs,
    (SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END)) AS gross_profit,
    SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
             THEN t.debit_amount - t.credit_amount ELSE 0 END) AS operating_expenses,
    (SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
              THEN t.debit_amount - t.credit_amount ELSE 0 END)) AS ebitda,
    SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0 END) AS depreciation_amortization,
    (SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
              THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0 END)) AS operating_income,
    SUM(CASE WHEN coa.sub_category = 'Interest Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END) AS interest_expense,
    (SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
              THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Interest Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END)) AS profit_before_tax,
    SUM(CASE WHEN coa.sub_category = 'Tax Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END) AS tax_expense,
    (SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
              THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Interest Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END) -
     SUM(CASE WHEN coa.sub_category = 'Tax Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END)) AS net_profit
FROM transactions t
JOIN chart_of_accounts coa ON t.account_id = coa.account_id
GROUP BY t.fiscal_year, t.fiscal_month
ORDER BY t.fiscal_year, t.fiscal_month;

-- Budget vs Actual View
CREATE OR REPLACE VIEW view_budget_vs_actual AS
WITH actual_spending AS (
    SELECT 
        t.fiscal_year,
        t.fiscal_month,
        t.department_id,
        t.account_id,
        SUM(CASE 
            WHEN coa.account_type = 'Expense' THEN t.debit_amount - t.credit_amount
            WHEN coa.account_type = 'Revenue' THEN t.credit_amount - t.debit_amount
            ELSE 0 END) AS actual_amount
    FROM transactions t
    JOIN chart_of_accounts coa ON t.account_id = coa.account_id
    GROUP BY t.fiscal_year, t.fiscal_month, t.department_id, t.account_id
)
SELECT 
    b.fiscal_year,
    b.fiscal_month,
    d.department_code,
    d.department_name,
    coa.account_code,
    coa.account_name,
    coa.account_type,
    b.budgeted_amount,
    COALESCE(a.actual_amount, 0) AS actual_amount,
    (COALESCE(a.actual_amount, 0) - b.budgeted_amount) AS variance_amount,
    CASE 
        WHEN b.budgeted_amount = 0 THEN 0.00
        ELSE ROUND(((COALESCE(a.actual_amount, 0) - b.budgeted_amount) / b.budgeted_amount) * 100.0, 2)
    END AS variance_percentage,
    CASE 
        WHEN coa.account_type = 'Expense' AND (COALESCE(a.actual_amount, 0) > b.budgeted_amount) THEN 'Over Budget'
        WHEN coa.account_type = 'Expense' AND (COALESCE(a.actual_amount, 0) <= b.budgeted_amount) THEN 'Within Budget'
        WHEN coa.account_type = 'Revenue' AND (COALESCE(a.actual_amount, 0) >= b.budgeted_amount) THEN 'Above Target'
        ELSE 'Below Target'
    END AS budget_status
FROM budgets b
JOIN departments d ON b.department_id = d.department_id
JOIN chart_of_accounts coa ON b.account_id = coa.account_id
LEFT JOIN actual_spending a ON b.fiscal_year = a.fiscal_year 
                            AND b.fiscal_month = a.fiscal_month 
                            AND b.department_id = a.department_id 
                            AND b.account_id = a.account_id;

-- Credit Risk Summary View
CREATE OR REPLACE VIEW view_credit_risk_summary AS
SELECT 
    l.loan_grade,
    COUNT(l.loan_id) AS total_loans,
    SUM(l.loan_amount) AS total_funded_amount,
    ROUND(AVG(l.loan_amount), 2) AS avg_loan_amount,
    ROUND(AVG(l.interest_rate), 2) AS avg_interest_rate,
    ROUND(AVG(l.debt_to_income_ratio), 2) AS avg_dti,
    SUM(l.is_default) AS total_defaults,
    ROUND((SUM(l.is_default)::NUMERIC / COUNT(l.loan_id)::NUMERIC) * 100.0, 2) AS default_rate_pct,
    ROUND(AVG(p.predicted_prob_default) * 100.0, 2) AS avg_predicted_default_prob_pct,
    ROUND(AVG(p.credit_score), 0) AS avg_credit_score
FROM loans l
LEFT JOIN credit_predictions p ON l.loan_id = p.loan_id
GROUP BY l.loan_grade
ORDER BY l.loan_grade;
