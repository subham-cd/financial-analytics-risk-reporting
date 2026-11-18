-- ============================================================================
-- FinSight Platform - Financial Intelligence & Credit Risk Reporting System
-- SQLite Relational Database Schema (Standard Local Engine)
-- Evaluation Project: Nexvia Technologies
-- ============================================================================

DROP VIEW IF EXISTS view_monthly_pnl;
DROP VIEW IF EXISTS view_balance_sheet;
DROP VIEW IF EXISTS view_budget_vs_actual;
DROP VIEW IF EXISTS view_credit_risk_summary;

DROP TABLE IF EXISTS financial_reports;
DROP TABLE IF EXISTS credit_predictions;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS borrowers;
DROP TABLE IF EXISTS equity;
DROP TABLE IF EXISTS liabilities;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS revenue;
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS chart_of_accounts;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_code TEXT NOT NULL UNIQUE,
    department_name TEXT NOT NULL,
    cost_center TEXT NOT NULL,
    manager_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chart_of_accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_code TEXT NOT NULL UNIQUE,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    normal_balance TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    account_id INTEGER NOT NULL REFERENCES chart_of_accounts(account_id),
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    transaction_category TEXT NOT NULL,
    debit_amount REAL NOT NULL DEFAULT 0.0,
    credit_amount REAL NOT NULL DEFAULT 0.0,
    description TEXT,
    reference_no TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    account_id INTEGER NOT NULL REFERENCES chart_of_accounts(account_id),
    budgeted_amount REAL NOT NULL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fiscal_year, fiscal_month, department_id, account_id)
);

CREATE TABLE revenue (
    revenue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER REFERENCES transactions(transaction_id),
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    stream_type TEXT NOT NULL,
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER REFERENCES transactions(transaction_id),
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    expense_category TEXT NOT NULL,
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code TEXT NOT NULL UNIQUE,
    asset_name TEXT NOT NULL,
    category TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    book_value REAL NOT NULL,
    accumulated_depreciation REAL NOT NULL DEFAULT 0.0,
    net_value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE liabilities (
    liability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    liability_code TEXT NOT NULL UNIQUE,
    liability_name TEXT NOT NULL,
    category TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    current_balance REAL NOT NULL,
    interest_rate REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equity (
    equity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    share_capital REAL NOT NULL,
    retained_earnings REAL NOT NULL,
    total_equity REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fiscal_year, fiscal_month)
);

CREATE TABLE borrowers (
    borrower_id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    annual_income REAL NOT NULL,
    employment_length_years REAL NOT NULL DEFAULT 0.0,
    home_ownership TEXT NOT NULL,
    state_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL REFERENCES borrowers(borrower_id),
    loan_amount REAL NOT NULL,
    loan_term_months INTEGER NOT NULL,
    interest_rate REAL NOT NULL,
    installment_amount REAL NOT NULL,
    loan_grade TEXT NOT NULL,
    debt_to_income_ratio REAL NOT NULL,
    revolving_utilization_pct REAL NOT NULL,
    total_credit_accounts INTEGER NOT NULL DEFAULT 0,
    open_credit_accounts INTEGER NOT NULL DEFAULT 0,
    derogatory_records INTEGER NOT NULL DEFAULT 0,
    loan_purpose TEXT NOT NULL,
    loan_status TEXT NOT NULL,
    is_default INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE credit_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER REFERENCES loans(loan_id),
    borrower_id INTEGER NOT NULL REFERENCES borrowers(borrower_id),
    predicted_prob_default REAL NOT NULL,
    credit_score INTEGER NOT NULL,
    risk_band TEXT NOT NULL,
    woe_score REAL,
    model_version TEXT NOT NULL DEFAULT 'v1.0.0-logistic-woe',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE financial_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name TEXT NOT NULL,
    report_period TEXT NOT NULL,
    report_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    generated_by TEXT DEFAULT 'FinSight-Engine',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_period ON transactions(fiscal_year, fiscal_month);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_department ON transactions(department_id);
CREATE INDEX idx_budgets_period ON budgets(fiscal_year, fiscal_month);
CREATE INDEX idx_loans_borrower ON loans(borrower_id);
CREATE INDEX idx_loans_status ON loans(loan_status);
CREATE INDEX idx_loans_grade ON loans(loan_grade);
CREATE INDEX idx_predictions_score ON credit_predictions(credit_score);
CREATE INDEX idx_predictions_risk ON credit_predictions(risk_band);

CREATE VIEW view_monthly_pnl AS
SELECT 
    t.fiscal_year,
    t.fiscal_month,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0.0 END), 2) AS total_revenue,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS cogs,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS gross_profit,
    ROUND(SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
                   THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS operating_expenses,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
                   THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS ebitda,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS depreciation_amortization,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
                   THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS operating_income,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Interest Expense' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS interest_expense,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
                   THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Interest Expense' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS profit_before_tax,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Tax Expense' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS tax_expense,
    ROUND(SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category IN ('Operating Expense', 'R&D', 'Sales & Marketing', 'General & Administrative') 
                   THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Depreciation & Amortization' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Interest Expense' THEN t.debit_amount - t.credit_amount ELSE 0.0 END) -
          SUM(CASE WHEN coa.sub_category = 'Tax Expense' THEN t.debit_amount - t.credit_amount ELSE 0.0 END), 2) AS net_profit
FROM transactions t
JOIN chart_of_accounts coa ON t.account_id = coa.account_id
GROUP BY t.fiscal_year, t.fiscal_month
ORDER BY t.fiscal_year, t.fiscal_month;

CREATE VIEW view_budget_vs_actual AS
WITH actual_spending AS (
    SELECT 
        t.fiscal_year,
        t.fiscal_month,
        t.department_id,
        t.account_id,
        SUM(CASE 
            WHEN coa.account_type = 'Expense' THEN t.debit_amount - t.credit_amount
            WHEN coa.account_type = 'Revenue' THEN t.credit_amount - t.debit_amount
            ELSE 0.0 END) AS actual_amount
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
    ROUND(b.budgeted_amount, 2) AS budgeted_amount,
    ROUND(COALESCE(a.actual_amount, 0.0), 2) AS actual_amount,
    ROUND(COALESCE(a.actual_amount, 0.0) - b.budgeted_amount, 2) AS variance_amount,
    CASE 
        WHEN b.budgeted_amount = 0 THEN 0.0
        ELSE ROUND(((COALESCE(a.actual_amount, 0.0) - b.budgeted_amount) / b.budgeted_amount) * 100.0, 2)
    END AS variance_percentage,
    CASE 
        WHEN coa.account_type = 'Expense' AND (COALESCE(a.actual_amount, 0.0) > b.budgeted_amount) THEN 'Over Budget'
        WHEN coa.account_type = 'Expense' AND (COALESCE(a.actual_amount, 0.0) <= b.budgeted_amount) THEN 'Within Budget'
        WHEN coa.account_type = 'Revenue' AND (COALESCE(a.actual_amount, 0.0) >= b.budgeted_amount) THEN 'Above Target'
        ELSE 'Below Target'
    END AS budget_status
FROM budgets b
JOIN departments d ON b.department_id = d.department_id
JOIN chart_of_accounts coa ON b.account_id = coa.account_id
LEFT JOIN actual_spending a ON b.fiscal_year = a.fiscal_year 
                            AND b.fiscal_month = a.fiscal_month 
                            AND b.department_id = a.department_id 
                            AND b.account_id = a.account_id;
