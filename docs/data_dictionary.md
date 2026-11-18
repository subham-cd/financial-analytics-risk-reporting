# FinSight – Database Data Dictionary

Comprehensive technical specification of all 13 relational tables and views within the FinSight database.

---

## 1. Core Corporate Master & Ledger Tables

### `departments`
Master table containing organizational units, cost centers, and leadership assignments.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `department_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique department identifier |
| `department_code` | VARCHAR(20) | NOT NULL, UNIQUE | 3-letter corporate code (e.g., ENG, SLS, MKT) |
| `department_name` | VARCHAR(100) | NOT NULL | Full corporate unit name |
| `cost_center` | VARCHAR(50) | NOT NULL | Financial ledger cost center (e.g., CC-101) |
| `manager_name` | VARCHAR(100) | NULLABLE | Department executive head |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit timestamp |

### `chart_of_accounts`
Standard GAAP chart of accounts defining taxonomy, normal balances, and financial statement classifications.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `account_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique general ledger account identifier |
| `account_code` | VARCHAR(20) | NOT NULL, UNIQUE | Standard 4-digit code (1000s-7000s) |
| `account_name` | VARCHAR(150) | NOT NULL | Descriptive line-item name |
| `account_type` | VARCHAR(50) | CHECK IN ('Asset','Liability','Equity','Revenue','Expense') | Master classification |
| `sub_category` | VARCHAR(100) | NOT NULL | Detailed grouping (Cash, COGS, R&D, etc.) |
| `normal_balance` | VARCHAR(10) | CHECK IN ('Debit', 'Credit') | Fundamental accounting balance side |
| `is_active` | INTEGER | DEFAULT 1 | Active posting flag |

### `transactions`
General journal double-entry transaction records.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Ledger entry transaction identifier |
| `transaction_date`| DATE | NOT NULL | Date transaction occurred |
| `fiscal_year` | INTEGER | NOT NULL | Fiscal accounting year (e.g., 2026) |
| `fiscal_month` | INTEGER | CHECK (1-12) | Accounting period month |
| `fiscal_quarter` | INTEGER | CHECK (1-4) | Accounting period quarter |
| `account_id` | INTEGER | FOREIGN KEY $\rightarrow$ chart_of_accounts | Debited or credited account |
| `department_id` | INTEGER | FOREIGN KEY $\rightarrow$ departments | Associated cost center |
| `transaction_category`| VARCHAR(50) | CHECK IN ('Operating','Financing','Investing','Adjusting') | Cash flow classification |
| `debit_amount` | REAL | NOT NULL, DEFAULT 0.0, CHECK (>=0) | Debited dollar amount |
| `credit_amount` | REAL | NOT NULL, DEFAULT 0.0, CHECK (>=0) | Credited dollar amount |
| `description` | TEXT | NULLABLE | Business memo / narrative |
| `reference_no` | VARCHAR(100) | NULLABLE | External invoice or voucher reference |

### `budgets`
Approved financial spending and revenue plan allocations.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `budget_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Budget line item identifier |
| `fiscal_year` | INTEGER | NOT NULL | Budget fiscal year |
| `fiscal_month` | INTEGER | CHECK (1-12) | Budget fiscal month |
| `department_id` | INTEGER | FOREIGN KEY $\rightarrow$ departments | Target organizational unit |
| `account_id` | INTEGER | FOREIGN KEY $\rightarrow$ chart_of_accounts | Target general ledger line |
| `budgeted_amount`| REAL | NOT NULL, DEFAULT 0.0 | Approved financial dollar target |
| `notes` | TEXT | NULLABLE | Strategic allocation notes |

---

## 2. Balance Sheet Ledgers

### `assets`
Monthly snapshot of company tangible, liquid, and fixed assets.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `asset_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Asset item record ID |
| `asset_code` | VARCHAR(50) | NOT NULL, UNIQUE | Asset inventory tag |
| `asset_name` | VARCHAR(150) | NOT NULL | Asset description |
| `category` | VARCHAR(100) | NOT NULL | Cash, AR, Inventory, Fixed Assets, etc. |
| `fiscal_year` | INTEGER | NOT NULL | Snapshot fiscal year |
| `fiscal_month` | INTEGER | NOT NULL | Snapshot fiscal month |
| `book_value` | REAL | NOT NULL | Gross historical purchase / recorded value |
| `accumulated_depreciation` | REAL | DEFAULT 0.0 | Cumulative depreciation against asset |
| `net_value` | REAL | NOT NULL | Book value minus accumulated depreciation |

### `liabilities`
Monthly snapshot of short-term and long-term corporate debt obligations.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `liability_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Liability record ID |
| `liability_code`| VARCHAR(50) | NOT NULL, UNIQUE | Debt facility reference code |
| `liability_name`| VARCHAR(150) | NOT NULL | Obligation description |
| `category` | VARCHAR(100) | NOT NULL | Accounts Payable, Short-Term Debt, etc. |
| `current_balance`| REAL | NOT NULL | Outstanding unpaid principal / balance |
| `interest_rate` | REAL | DEFAULT 0.0 | Annual contractual interest percentage |

### `equity`
Monthly snapshot of paid-in shareholder capital and retained corporate earnings.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `equity_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Equity record ID |
| `fiscal_year` | INTEGER | NOT NULL | Fiscal year |
| `fiscal_month` | INTEGER | NOT NULL | Fiscal month |
| `share_capital` | REAL | NOT NULL | Paid-in equity capital from shareholders |
| `retained_earnings` | REAL | NOT NULL | Cumulative net profit retained in business |
| `total_equity` | REAL | NOT NULL | Share Capital + Retained Earnings |

---

## 3. Credit Risk & Machine Learning Tables

### `borrowers`
Borrower demographic, employment, and income profiles.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `borrower_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal borrower identifier |
| `external_id` | VARCHAR(50) | NOT NULL, UNIQUE | External bureau identifier (e.g. BOR-100001) |
| `first_name` | VARCHAR(100) | NOT NULL | Borrower first name |
| `last_name` | VARCHAR(100) | NOT NULL | Borrower surname |
| `annual_income`| REAL | NOT NULL, CHECK (>0) | Verified gross annual earnings |
| `employment_length_years`| REAL | DEFAULT 0.0 | Total years in current employment |
| `home_ownership`| VARCHAR(20) | CHECK IN ('RENT','OWN','MORTGAGE','OTHER') | Housing arrangement |
| `state_code` | VARCHAR(10) | NULLABLE | US state residential code |

### `loans`
Lending Club-standard credit terms and bureau performance attributes.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `loan_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Loan file identifier |
| `borrower_id` | INTEGER | FOREIGN KEY $\rightarrow$ borrowers | Associated borrower |
| `loan_amount` | REAL | NOT NULL, CHECK (>0) | Approved principal amount |
| `loan_term_months` | INTEGER | CHECK IN (36, 60) | Amortization term in months |
| `interest_rate` | REAL | NOT NULL | Approved APR percentage |
| `installment_amount` | REAL | NOT NULL | Monthly contractual installment ($) |
| `loan_grade` | VARCHAR(5) | CHECK IN ('A','B','C','D','E','F') | Risk grade |
| `debt_to_income_ratio`| REAL | NOT NULL | Monthly debt payments / gross monthly income (%) |
| `revolving_utilization_pct`| REAL| NOT NULL | Total credit line balance / credit limit (%) |
| `total_credit_accounts` | INTEGER| DEFAULT 0 | Total credit accounts on file |
| `open_credit_accounts` | INTEGER | DEFAULT 0 | Currently open credit accounts |
| `derogatory_records` | INTEGER | DEFAULT 0 | Public derogatory records / bankruptcies |
| `loan_purpose` | VARCHAR(50) | NOT NULL | Declared borrowing intent |
| `loan_status` | VARCHAR(50) | CHECK IN ('Fully Paid','Charged Off') | Terminal loan performance status |
| `is_default` | INTEGER | CHECK IN (0, 1) | Binary target: 0 = Good, 1 = Default |

### `credit_predictions`
Model inference scores, default probabilities, and risk tiers.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `prediction_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Prediction record ID |
| `loan_id` | INTEGER | FOREIGN KEY $\rightarrow$ loans | Associated loan file |
| `borrower_id` | INTEGER | FOREIGN KEY $\rightarrow$ borrowers | Scored borrower |
| `predicted_prob_default`| REAL | CHECK (0.0 to 1.0) | Calibrated default probability from Logistic Model |
| `credit_score` | INTEGER | CHECK (300 to 850) | FICO-scaled scorecard value |
| `risk_band` | VARCHAR(20) | CHECK IN ('Low Risk','Medium Risk','High Risk','Very High Risk') | Underwriting risk tier |
| `woe_score` | REAL | NULLABLE | Cumulative Weight of Evidence score |
| `model_version` | VARCHAR(50) | DEFAULT 'v1.0.0-logistic-woe' | Tracking identifier |
