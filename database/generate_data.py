"""
FinSight Platform - Financial & Credit Risk Data Generation Engine
Generates:
1. Reconciled Double-Entry Financial Ledger (P&L, Balance Sheet, Budget vs Actual)
2. Lending Club-Style Credit Risk Borrower & Loan Dataset
3. Loads data into SQLite database (finsight.db) and exports CSV archives
"""

import os
import sqlite3
import random
import numpy as np
import pandas as pd
from datetime import datetime, date

# Seed for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "finsight.db")
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
SCHEMA_SQL_PATH = os.path.join(BASE_DIR, "database", "schema_sqlite.sql")

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

print(f"[*] Initializing FinSight Data Generation...")
print(f"[*] Database Path: {DB_PATH}")

# -----------------------------------------------------------------------------
# 1. Departments Master Data
# -----------------------------------------------------------------------------
DEPARTMENTS = [
    {"department_code": "ENG", "department_name": "Engineering & Technology", "cost_center": "CC-101", "manager_name": "Elena Rostova"},
    {"department_code": "SLS", "department_name": "Enterprise Sales", "cost_center": "CC-102", "manager_name": "Marcus Vance"},
    {"department_code": "MKT", "department_name": "Product Marketing & Growth", "cost_center": "CC-103", "manager_name": "Sarah Jenkins"},
    {"department_code": "OPS", "department_name": "Cloud Operations & Support", "cost_center": "CC-104", "manager_name": "David Kim"},
    {"department_code": "GNA", "department_name": "General & Administration", "cost_center": "CC-105", "manager_name": "Arthur Pendelton"},
    {"department_code": "FIN", "department_name": "Finance & Corporate Strategy", "cost_center": "CC-106", "manager_name": "Sophia Chen"},
    {"department_code": "CSU", "department_name": "Customer Success & Onboarding", "cost_center": "CC-107", "manager_name": "Liam O'Connor"},
]

# -----------------------------------------------------------------------------
# 2. Chart of Accounts Master Data
# Standard GAAP taxonomy
# -----------------------------------------------------------------------------
CHART_OF_ACCOUNTS = [
    # Assets (1000s)
    {"account_code": "1010", "account_name": "Cash and Cash Equivalents", "account_type": "Asset", "sub_category": "Cash", "normal_balance": "Debit"},
    {"account_code": "1020", "account_name": "Accounts Receivable", "account_type": "Asset", "sub_category": "Accounts Receivable", "normal_balance": "Debit"},
    {"account_code": "1030", "account_name": "Commercial Inventory & Prepaids", "account_type": "Asset", "sub_category": "Inventory", "normal_balance": "Debit"},
    {"account_code": "1510", "account_name": "Property, Plant & Equipment", "account_type": "Asset", "sub_category": "Fixed Assets", "normal_balance": "Debit"},
    {"account_code": "1520", "account_name": "Intangible Tech Assets & IP", "account_type": "Asset", "sub_category": "Fixed Assets", "normal_balance": "Debit"},
    {"account_code": "1590", "account_name": "Accumulated Depreciation", "account_type": "Asset", "sub_category": "Contra-Asset", "normal_balance": "Credit"},
    {"account_code": "1810", "account_name": "Long-Term Security Deposits & Other", "account_type": "Asset", "sub_category": "Other Assets", "normal_balance": "Debit"},

    # Liabilities (2000s)
    {"account_code": "2010", "account_name": "Accounts Payable", "account_type": "Liability", "sub_category": "Accounts Payable", "normal_balance": "Credit"},
    {"account_code": "2020", "account_name": "Short-Term Revolving Credit Facility", "account_type": "Liability", "sub_category": "Short-Term Debt", "normal_balance": "Credit"},
    {"account_code": "2030", "account_name": "Accrued Payroll & Operational Expenses", "account_type": "Liability", "sub_category": "Other Liabilities", "normal_balance": "Credit"},
    {"account_code": "2510", "account_name": "Senior Long-Term Bank Notes", "account_type": "Liability", "sub_category": "Long-Term Debt", "normal_balance": "Credit"},

    # Equity (3000s)
    {"account_code": "3010", "account_name": "Common Stock & Paid-in Capital", "account_type": "Equity", "sub_category": "Share Capital", "normal_balance": "Credit"},
    {"account_code": "3020", "account_name": "Retained Earnings", "account_type": "Equity", "sub_category": "Retained Earnings", "normal_balance": "Credit"},

    # Revenue (4000s)
    {"account_code": "4010", "account_name": "Enterprise SaaS Subscriptions", "account_type": "Revenue", "sub_category": "Revenue", "normal_balance": "Credit"},
    {"account_code": "4020", "account_name": "Professional Services & Advisory", "account_type": "Revenue", "sub_category": "Revenue", "normal_balance": "Credit"},
    {"account_code": "4030", "account_name": "Platform API & Usage Fees", "account_type": "Revenue", "sub_category": "Revenue", "normal_balance": "Credit"},

    # Cost of Goods Sold (5000s)
    {"account_code": "5010", "account_name": "Hosting & Cloud Infrastructure COGS", "account_type": "Expense", "sub_category": "Cost of Goods Sold", "normal_balance": "Debit"},
    {"account_code": "5020", "account_name": "Direct Client Implementation Labor COGS", "account_type": "Expense", "sub_category": "Cost of Goods Sold", "normal_balance": "Debit"},

    # Operating Expenses (6000s)
    {"account_code": "6010", "account_name": "Research & Product Engineering", "account_type": "Expense", "sub_category": "R&D", "normal_balance": "Debit"},
    {"account_code": "6020", "account_name": "Sales Campaigns & Acquisition Commissions", "account_type": "Expense", "sub_category": "Sales & Marketing", "normal_balance": "Debit"},
    {"account_code": "6030", "account_name": "General, Administrative & Legal", "account_type": "Expense", "sub_category": "General & Administrative", "normal_balance": "Debit"},
    {"account_code": "6040", "account_name": "Depreciation & Amortization Expense", "account_type": "Expense", "sub_category": "Depreciation & Amortization", "normal_balance": "Debit"},

    # Non-Operating / Tax (7000s)
    {"account_code": "7010", "account_name": "Corporate Debt Interest Expense", "account_type": "Expense", "sub_category": "Interest Expense", "normal_balance": "Debit"},
    {"account_code": "7020", "account_name": "Corporate Income Tax Expense", "account_type": "Expense", "sub_category": "Tax Expense", "normal_balance": "Debit"},
]

def generate_financial_ledger():
    """Generates monthly transactions, budgets, P&L, and reconciled Balance Sheet for 2026."""
    print("[*] Generating 12-month double-entry financial ledger for FY 2026...")
    
    months = list(range(1, 13))
    fiscal_year = 2026
    
    # Base monthly budget values (approximate monthly scale ~$1.8M - $2.4M revenue)
    monthly_budget_revenue = {
        1: 1850000, 2: 1900000, 3: 2050000, 4: 2000000,
        5: 2150000, 6: 2250000, 7: 2200000, 8: 2300000,
        9: 2450000, 10: 2500000, 11: 2600000, 12: 2800000
    }
    
    # Revenue split
    rev_split = {"4010": 0.70, "4020": 0.18, "4030": 0.12}
    
    # Budgeted expense proportions relative to budgeted revenue
    # COGS ~22%, R&D ~20%, Sales & Marketing ~22%, G&A ~12%, Depr ~$45K, Interest ~$25K
    budget_records = []
    transaction_records = []
    revenue_records = []
    expense_records = []
    
    tx_counter = 1000
    
    # Initial balance sheet values at start of 2026 (December 31, 2025)
    # Total Assets = $18,500,000 | Liabilities = $7,000,000 | Equity = $11,500,000
    base_cash = 6500000.0
    base_ar = 2200000.0
    base_inventory = 800000.0
    base_fixed_assets = 10000000.0
    base_acc_depr = 1500000.0
    base_other_assets = 500000.0
    
    base_ap = 1800000.0
    base_st_debt = 1200000.0
    base_lt_debt = 3200000.0
    base_other_liab = 800000.0
    
    share_capital = 8000000.0
    retained_earnings = 3500000.0  # $18.5M - $7.0M - $8.0M = $3.5M
    
    asset_history = []
    liability_history = []
    equity_history = []
    
    for m in months:
        b_rev = monthly_budget_revenue[m]
        
        # 1. Budget records for Revenue
        for acc_code, pct in rev_split.items():
            b_amt = round(b_rev * pct, 2)
            budget_records.append({
                "fiscal_year": fiscal_year, "fiscal_month": m,
                "department_code": "SLS", "account_code": acc_code,
                "budgeted_amount": b_amt,
                "notes": f"FY2026-M{m} Revenue target for {acc_code}"
            })
            
        # 2. Budget records for Expenses
        cogs_budget = b_rev * 0.22
        rnd_budget = b_rev * 0.20
        mkt_budget = b_rev * 0.22
        gna_budget = b_rev * 0.12
        depr_budget = 45000.0
        interest_budget = 25000.0
        
        exp_budgets = [
            ("OPS", "5010", cogs_budget * 0.60),
            ("CSU", "5020", cogs_budget * 0.40),
            ("ENG", "6010", rnd_budget),
            ("SLS", "6020", mkt_budget * 0.55),
            ("MKT", "6020", mkt_budget * 0.45),
            ("GNA", "6030", gna_budget),
            ("OPS", "6040", depr_budget),
            ("FIN", "7010", interest_budget),
        ]
        
        for dept_code, acc_code, amt in exp_budgets:
            budget_records.append({
                "fiscal_year": fiscal_year, "fiscal_month": m,
                "department_code": dept_code, "account_code": acc_code,
                "budgeted_amount": round(amt, 2),
                "notes": f"Budget allocation for {dept_code} - {acc_code}"
            })
            
        # ---------------------------------------------------------------------
        # Actual Transactions for Month m
        # Realistic variations:
        # Seasonality / growth: Actual revenue varies by -3% to +7% of budget
        # ---------------------------------------------------------------------
        rev_multiplier = 1.0 + random.uniform(-0.03, 0.07)
        # In Q4 (M10, M11, M12) strong enterprise closing:
        if m in [10, 11, 12]:
            rev_multiplier += random.uniform(0.02, 0.05)
            
        act_rev_total = b_rev * rev_multiplier
        
        # Revenue transactions
        actual_rev_dict = {}
        for acc_code, pct in rev_split.items():
            tx_counter += 1
            amt = round(act_rev_total * pct, 2)
            actual_rev_dict[acc_code] = amt
            
            # Booking Revenue (Credit Revenue, Debit Cash/AR)
            tx_date = f"{fiscal_year}-{m:02d}-{random.randint(20, 28):02d}"
            q = (m - 1) // 3 + 1
            transaction_records.append({
                "transaction_id": tx_counter,
                "transaction_date": tx_date,
                "fiscal_year": fiscal_year,
                "fiscal_month": m,
                "fiscal_quarter": q,
                "account_code": acc_code,
                "department_code": "SLS",
                "transaction_category": "Operating",
                "debit_amount": 0.0,
                "credit_amount": amt,
                "description": f"Customer Billings & Platform Collections M{m}",
                "reference_no": f"INV-2026-{m:02d}-{random.randint(1000, 9999)}"
            })
            revenue_records.append({
                "transaction_id": tx_counter,
                "fiscal_year": fiscal_year,
                "fiscal_month": m,
                "department_code": "SLS",
                "stream_type": "Enterprise Subscriptions" if acc_code == "4010" else ("Professional Services" if acc_code == "4020" else "API Usage Fees"),
                "amount": amt
            })
            
        actual_total_revenue = sum(actual_rev_dict.values())
        
        # Actual Expenses:
        # COGS fluctuates with server usage
        act_cogs_5010 = round(cogs_budget * 0.60 * random.uniform(0.95, 1.08), 2)
        act_cogs_5020 = round(cogs_budget * 0.40 * random.uniform(0.96, 1.04), 2)
        
        # Engineering R&D: hiring causes slight overspend in mid-year
        eng_factor = 1.06 if m in [5, 6, 7, 8] else random.uniform(0.98, 1.03)
        act_rnd_6010 = round(rnd_budget * eng_factor, 2)
        
        # Sales commissions: tied to revenue performance
        act_sales_6020 = round(mkt_budget * 0.55 * (rev_multiplier), 2)
        act_mkt_6020 = round(mkt_budget * 0.45 * random.uniform(0.94, 1.05), 2)
        
        # G&A
        act_gna_6030 = round(gna_budget * random.uniform(0.95, 1.02), 2)
        
        # D&A is constant / gradual
        act_depr_6040 = 45000.0
        
        # Interest
        act_interest_7010 = 24500.0
        
        actual_expenses_list = [
            ("OPS", "5010", act_cogs_5010, "Cloud hosting cluster compute & storage"),
            ("CSU", "5020", act_cogs_5020, "Dedicated customer engineering onboarding"),
            ("ENG", "6010", act_rnd_6010, "Core platform & model development engineering"),
            ("SLS", "6020", act_sales_6020, "Account executive sales compensation & commissions"),
            ("MKT", "6020", act_mkt_6020, "Enterprise digital acquisition & event campaigns"),
            ("GNA", "6030", act_gna_6030, "Executive management, facilities & legal overhead"),
            ("OPS", "6040", act_depr_6040, "Monthly tangible asset and server depreciation"),
            ("FIN", "7010", act_interest_7010, "Senior bank facility monthly interest charge"),
        ]
        
        for dept_code, acc_code, amt, desc in actual_expenses_list:
            tx_counter += 1
            tx_date = f"{fiscal_year}-{m:02d}-{random.randint(15, 27):02d}"
            transaction_records.append({
                "transaction_id": tx_counter,
                "transaction_date": tx_date,
                "fiscal_year": fiscal_year,
                "fiscal_month": m,
                "fiscal_quarter": (m - 1) // 3 + 1,
                "account_code": acc_code,
                "department_code": dept_code,
                "transaction_category": "Operating" if acc_code != "7010" else "Financing",
                "debit_amount": amt,
                "credit_amount": 0.0,
                "description": desc,
                "reference_no": f"EXP-2026-{m:02d}-{random.randint(1000, 9999)}"
            })
            expense_records.append({
                "transaction_id": tx_counter,
                "fiscal_year": fiscal_year,
                "fiscal_month": m,
                "department_code": dept_code,
                "expense_category": "COGS" if acc_code.startswith("5") else ("Operating" if acc_code.startswith("6") else "Interest"),
                "amount": amt
            })
            
        # P&L Calculation for the month
        cogs = act_cogs_5010 + act_cogs_5020
        gross_profit = actual_total_revenue - cogs
        opex = act_rnd_6010 + act_sales_6020 + act_mkt_6020 + act_gna_6030
        ebitda = gross_profit - opex
        operating_income = ebitda - act_depr_6040
        pbt = operating_income - act_interest_7010
        tax_expense = round(max(0.0, pbt * 0.21), 2)  # 21% US Corporate Tax Rate
        net_profit = round(pbt - tax_expense, 2)
        
        # Record Tax Transaction
        tx_counter += 1
        transaction_records.append({
            "transaction_id": tx_counter,
            "transaction_date": f"{fiscal_year}-{m:02d}-28",
            "fiscal_year": fiscal_year,
            "fiscal_month": m,
            "fiscal_quarter": (m - 1) // 3 + 1,
            "account_code": "7020",
            "department_code": "FIN",
            "transaction_category": "Adjusting",
            "debit_amount": tax_expense,
            "credit_amount": 0.0,
            "description": "Monthly corporate income tax accrual",
            "reference_no": f"TAX-2026-{m:02d}"
        })
        expense_records.append({
            "transaction_id": tx_counter,
            "fiscal_year": fiscal_year,
            "fiscal_month": m,
            "department_code": "FIN",
            "expense_category": "Tax",
            "amount": tax_expense
        })
        
        # ---------------------------------------------------------------------
        # Balance Sheet Update & Reconciliation (Strict GAAP Equation)
        # Assets = Liabilities + Equity
        # ---------------------------------------------------------------------
        retained_earnings += net_profit
        base_acc_depr += act_depr_6040
        
        # AR fluctuates with revenue (~1.1x monthly revenue)
        curr_ar = round(actual_total_revenue * random.uniform(1.05, 1.15), 2)
        # AP fluctuates with opex/cogs (~0.8x monthly expenses)
        curr_ap = round((cogs + opex) * random.uniform(0.75, 0.85), 2)
        curr_inventory = round(base_inventory * (1.0 + (m * 0.01)), 2)
        curr_other_assets = base_other_assets
        curr_fixed_assets = base_fixed_assets
        
        # Debt amortization: paying down $25k short-term debt per month
        curr_st_debt = round(max(500000.0, base_st_debt - (m * 25000.0)), 2)
        curr_lt_debt = round(base_lt_debt - (m * 15000.0), 2)
        curr_other_liab = base_other_liab
        
        total_curr_liabilities = curr_ap + curr_st_debt + curr_lt_debt + curr_other_liab
        total_curr_equity = share_capital + retained_earnings
        
        # Target Total Assets must strictly equal Liabilities + Equity!
        target_total_assets = total_curr_liabilities + total_curr_equity
        
        # Cash is the balancing account in financial reconciliation
        # Cash = Target Total Assets - (AR + Inventory + Net Fixed Assets + Other Assets)
        net_fixed_assets = curr_fixed_assets - base_acc_depr
        curr_cash = round(target_total_assets - (curr_ar + curr_inventory + net_fixed_assets + curr_other_assets), 2)
        
        # Verify reconciliation
        total_calc_assets = round(curr_cash + curr_ar + curr_inventory + net_fixed_assets + curr_other_assets, 2)
        total_calc_liab_eq = round(total_curr_liabilities + total_curr_equity, 2)
        discrepancy = round(total_calc_assets - total_calc_liab_eq, 2)
        assert abs(discrepancy) == 0.0, f"Discrepancy in month {m}: {discrepancy}"
        
        # Store monthly balance sheet snapshots
        asset_snapshots = [
            ("AST-1010", "Cash and Cash Equivalents", "Cash", curr_cash, 0.0),
            ("AST-1020", "Accounts Receivable", "Accounts Receivable", curr_ar, 0.0),
            ("AST-1030", "Commercial Inventory & Prepaids", "Inventory", curr_inventory, 0.0),
            ("AST-1510", "Property, Plant & Equipment", "Fixed Assets", curr_fixed_assets, base_acc_depr),
            ("AST-1810", "Security Deposits & Other Assets", "Other Assets", curr_other_assets, 0.0),
        ]
        for acode, aname, acat, bval, dep in asset_snapshots:
            asset_history.append({
                "asset_code": f"{acode}-M{m:02d}",
                "asset_name": aname,
                "category": acat,
                "fiscal_year": fiscal_year,
                "fiscal_month": m,
                "book_value": bval,
                "accumulated_depreciation": dep,
                "net_value": round(bval - dep, 2)
            })
            
        liab_snapshots = [
            ("LIA-2010", "Trade Accounts Payable", "Accounts Payable", curr_ap, 0.0),
            ("LIA-2020", "Revolving Credit Line", "Short-Term Debt", curr_st_debt, 6.25),
            ("LIA-2030", "Accrued Operational Liabilities", "Other Liabilities", curr_other_liab, 0.0),
            ("LIA-2510", "Senior Long-Term Bank Notes", "Long-Term Debt", curr_lt_debt, 5.50),
        ]
        for lcode, lname, lcat, bal, irate in liab_snapshots:
            liability_history.append({
                "liability_code": f"{lcode}-M{m:02d}",
                "liability_name": lname,
                "category": lcat,
                "fiscal_year": fiscal_year,
                "fiscal_month": m,
                "current_balance": bal,
                "interest_rate": irate
            })
            
        equity_history.append({
            "fiscal_year": fiscal_year,
            "fiscal_month": m,
            "share_capital": share_capital,
            "retained_earnings": round(retained_earnings, 2),
            "total_equity": round(total_curr_equity, 2)
        })
        
    print(f"[+] Successfully generated {len(transaction_records)} financial ledger transactions.")
    print(f"[+] Successfully generated {len(budget_records)} budget line items.")
    print(f"[+] Financial statements strictly reconciled: Assets = Liabilities + Equity (Diff = $0.00).")
    
    return {
        "transactions": transaction_records,
        "budgets": budget_records,
        "revenue": revenue_records,
        "expenses": expense_records,
        "assets": asset_history,
        "liabilities": liability_history,
        "equity": equity_history
    }

# -----------------------------------------------------------------------------
# 3. Credit Risk Dataset Generator (Lending Club Standard)
# -----------------------------------------------------------------------------
def generate_credit_risk_dataset(n_samples=5000):
    """
    Generates a realistic credit risk dataset based on Lending Club statistical distributions:
    Features:
    - Annual Income: lognormal distribution
    - Debt-to-Income (DTI): Beta/gamma distribution
    - Loan Amount: $1,000 - $40,000
    - Loan Term: 36 or 60 months
    - Loan Grade: A (lowest risk) to F (highest risk)
    - Interest Rate: strongly correlated with Loan Grade
    - Revolving Credit Utilization: 0% - 100%
    - Total / Open Credit Accounts
    - Derogatory Records
    - Default Indicator (is_default: 0 = Fully Paid, 1 = Default)
    """
    print(f"[*] Generating {n_samples} borrower and loan credit risk records...")
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]
    states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "NJ", "VA", "WA", "AZ", "MA", "CO"]
    purposes = ["debt_consolidation", "credit_card", "home_improvement", "small_business", "major_purchase", "medical"]
    
    borrowers = []
    loans = []
    
    grades = ["A", "B", "C", "D", "E", "F"]
    grade_probs = [0.20, 0.30, 0.25, 0.14, 0.08, 0.03]
    
    # Grade baseline default odds and interest rate ranges
    grade_config = {
        "A": {"base_ir": (5.5, 9.0), "default_prob": 0.05},
        "B": {"base_ir": (9.0, 13.0), "default_prob": 0.11},
        "C": {"base_ir": (13.0, 17.5), "default_prob": 0.18},
        "D": {"base_ir": (17.5, 22.0), "default_prob": 0.28},
        "E": {"base_ir": (22.0, 26.5), "default_prob": 0.39},
        "F": {"base_ir": (26.5, 30.0), "default_prob": 0.52},
    }
    
    for i in range(1, n_samples + 1):
        ext_id = f"BOR-{100000 + i}"
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        
        # Annual Income (log-normal, mean ~$75k)
        income = float(np.round(np.random.lognormal(mean=11.1, sigma=0.55), -2))
        income = min(max(income, 22000.0), 320000.0)
        
        emp_len = float(np.random.choice([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0], p=[0.08, 0.09, 0.12, 0.11, 0.10, 0.15, 0.15, 0.20]))
        home_own = np.random.choice(["RENT", "MORTGAGE", "OWN", "OTHER"], p=[0.42, 0.46, 0.11, 0.01])
        state = random.choice(states)
        
        borrowers.append({
            "borrower_id": i,
            "external_id": ext_id,
            "first_name": fn,
            "last_name": ln,
            "annual_income": income,
            "employment_length_years": emp_len,
            "home_ownership": home_own,
            "state_code": state
        })
        
        # Loan Assignment
        grade = np.random.choice(grades, p=grade_probs)
        conf = grade_config[grade]
        
        # Loan Amount: $1,000 to $40,000 (correlated with income)
        max_loan_by_inc = income * 0.45
        amt = float(np.round(min(random.uniform(2500, 38000), max_loan_by_inc), -2))
        amt = max(amt, 1500.0)
        
        term = int(np.random.choice([36, 60], p=[0.72, 0.28]))
        irate = round(random.uniform(*conf["base_ir"]), 2)
        
        # Monthly Installment
        # P * (r*(1+r)^n) / ((1+r)^n - 1)
        monthly_r = (irate / 100.0) / 12.0
        installment = round(amt * (monthly_r * (1 + monthly_r)**term) / ((1 + monthly_r)**term - 1), 2)
        
        # DTI: Debt-to-income (percentage)
        # Higher grade -> lower DTI
        base_dti = {"A": 12.0, "B": 16.0, "C": 21.0, "D": 26.0, "E": 30.0, "F": 35.0}[grade]
        dti = round(min(max(np.random.normal(base_dti, 6.0), 3.0), 48.0), 2)
        
        # Revolving utilization
        base_rev_util = {"A": 25.0, "B": 42.0, "C": 58.0, "D": 72.0, "E": 82.0, "F": 89.0}[grade]
        rev_util = round(min(max(np.random.normal(base_rev_util, 15.0), 0.0), 99.9), 2)
        
        total_acc = int(np.random.poisson(lam=18))
        open_acc = max(2, min(total_acc, int(np.random.poisson(lam=10))))
        
        # Derogatory records
        derog_prob = {"A": 0.02, "B": 0.06, "C": 0.12, "D": 0.22, "E": 0.35, "F": 0.48}[grade]
        derog = int(np.random.choice([0, 1, 2, 3], p=[1 - derog_prob, derog_prob * 0.7, derog_prob * 0.2, derog_prob * 0.1]))
        
        purpose = np.random.choice(purposes, p=[0.50, 0.22, 0.10, 0.08, 0.06, 0.04])
        
        # Default Logic driven by mathematical logit function
        # Log-odds of default = beta_0 + beta_grade + beta_dti + beta_util + beta_derog - beta_income
        logit = (
            -1.1 
            + ({"A": -1.2, "B": -0.5, "C": 0.3, "D": 0.9, "E": 1.5, "F": 2.2}[grade])
            + (dti * 0.035)
            + (rev_util * 0.015)
            + (derog * 0.35)
            - (np.log(income) * 0.25)
            + (1.0 if term == 60 else 0.0) * 0.25
        )
        prob_default = 1.0 / (1.0 + np.exp(-logit))
        is_default = 1 if np.random.rand() < prob_default else 0
        loan_status = "Charged Off" if is_default == 1 else "Fully Paid"
        
        loans.append({
            "loan_id": i,
            "borrower_id": i,
            "loan_amount": amt,
            "loan_term_months": term,
            "interest_rate": irate,
            "installment_amount": installment,
            "loan_grade": grade,
            "debt_to_income_ratio": dti,
            "revolving_utilization_pct": rev_util,
            "total_credit_accounts": total_acc,
            "open_credit_accounts": open_acc,
            "derogatory_records": derog,
            "loan_purpose": purpose,
            "loan_status": loan_status,
            "is_default": is_default
        })
        
    df_loans = pd.DataFrame(loans)
    print(f"[+] Credit dataset generated: {len(loans)} loans.")
    print(f"[+] Overall Default Rate: {(df_loans['is_default'].mean() * 100):.2f}%")
    for g in grades:
        sub = df_loans[df_loans["loan_grade"] == g]
        print(f"    - Grade {g}: Count={len(sub)}, Default Rate={(sub['is_default'].mean() * 100):.2f}%")
        
    return borrowers, loans

def populate_database():
    """Initializes schema and populates SQLite database with generated datasets."""
    print(f"[*] Connecting to SQLite database at {DB_PATH}...")
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("[*] Removed existing database file for clean build.")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Execute schema DDL
    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        schema_ddl = f.read()
    cursor.executescript(schema_ddl)
    print("[+] Database schema created successfully.")
    
    # 1. Insert Departments
    dept_df = pd.DataFrame(DEPARTMENTS)
    dept_df.to_sql("departments", conn, if_exists="append", index=False)
    print(f"[+] Loaded {len(DEPARTMENTS)} departments.")
    
    # Retrieve department map (code -> id)
    dept_map = dict(cursor.execute("SELECT department_code, department_id FROM departments").fetchall())
    
    # 2. Insert Chart of Accounts
    coa_df = pd.DataFrame(CHART_OF_ACCOUNTS)
    coa_df["is_active"] = 1
    coa_df.to_sql("chart_of_accounts", conn, if_exists="append", index=False)
    print(f"[+] Loaded {len(CHART_OF_ACCOUNTS)} chart of accounts.")
    
    # Retrieve account map (code -> id)
    coa_map = dict(cursor.execute("SELECT account_code, account_id FROM chart_of_accounts").fetchall())
    
    # 3. Generate and Insert Financial Ledger Data
    fin_data = generate_financial_ledger()
    
    # Transactions
    tx_df = pd.DataFrame(fin_data["transactions"])
    tx_df["account_id"] = tx_df["account_code"].map(coa_map)
    tx_df["department_id"] = tx_df["department_code"].map(dept_map)
    tx_db_df = tx_df.drop(columns=["account_code", "department_code"])
    tx_db_df.to_sql("transactions", conn, if_exists="append", index=False)
    print(f"[+] Loaded {len(tx_db_df)} transactions.")
    
    # Budgets
    b_df = pd.DataFrame(fin_data["budgets"])
    b_df["account_id"] = b_df["account_code"].map(coa_map)
    b_df["department_id"] = b_df["department_code"].map(dept_map)
    b_db_df = b_df.drop(columns=["account_code", "department_code"])
    b_db_df.to_sql("budgets", conn, if_exists="append", index=False)
    print(f"[+] Loaded {len(b_db_df)} budget lines.")
    
    # Revenue & Expenses
    rev_df = pd.DataFrame(fin_data["revenue"])
    rev_df["department_id"] = rev_df["department_code"].map(dept_map)
    rev_df.drop(columns=["department_code"]).to_sql("revenue", conn, if_exists="append", index=False)
    
    exp_df = pd.DataFrame(fin_data["expenses"])
    exp_df["department_id"] = exp_df["department_code"].map(dept_map)
    exp_df.drop(columns=["department_code"]).to_sql("expenses", conn, if_exists="append", index=False)
    
    # Assets, Liabilities, Equity
    pd.DataFrame(fin_data["assets"]).to_sql("assets", conn, if_exists="append", index=False)
    pd.DataFrame(fin_data["liabilities"]).to_sql("liabilities", conn, if_exists="append", index=False)
    pd.DataFrame(fin_data["equity"]).to_sql("equity", conn, if_exists="append", index=False)
    print("[+] Loaded Assets, Liabilities, and Equity ledgers.")
    
    # 4. Generate and Insert Credit Risk Data
    borrowers, loans = generate_credit_risk_dataset(n_samples=5000)
    bor_df = pd.DataFrame(borrowers)
    loans_df = pd.DataFrame(loans)
    
    bor_df.to_sql("borrowers", conn, if_exists="append", index=False)
    loans_df.to_sql("loans", conn, if_exists="append", index=False)
    print(f"[+] Loaded {len(bor_df)} borrowers and {len(loans_df)} loans.")
    
    # Save raw CSV archives for reproducibility
    bor_df.to_csv(os.path.join(RAW_DATA_DIR, "borrowers_raw.csv"), index=False)
    loans_df.to_csv(os.path.join(RAW_DATA_DIR, "loans_raw.csv"), index=False)
    tx_df.to_csv(os.path.join(RAW_DATA_DIR, "transactions_ledger_raw.csv"), index=False)
    b_df.to_csv(os.path.join(RAW_DATA_DIR, "budgets_raw.csv"), index=False)
    
    conn.commit()
    conn.close()
    print("[SUCCESS] All data generated and stored into finsight.db successfully.")

if __name__ == "__main__":
    populate_database()
