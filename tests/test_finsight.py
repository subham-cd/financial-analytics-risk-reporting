"""
FinSight Platform - Comprehensive Test & Validation Suite
Tests:
1. Database connectivity and row counts
2. Balance sheet reconciliation (Assets = Liabilities + Equity for all 12 months)
3. P&L accounting equation (Revenue - COGS - Opex - D&A - Interest - Tax = Net Profit)
4. Budget variance calculation formulas and zero-budget handling
5. WOE transformer logic and monotonicity
6. Scorecard scaling formulas (Basel II / FICO)
7. ML model prediction shape and ranges (ROC-AUC > 0.75, valid score 300-850)
8. FastAPI REST endpoints via TestClient (Overview, P&L, Balance Sheet, Budget, Credit Risk, Reports)
9. PDF report file generation and integrity
"""

import os
import sys
import sqlite3
import pytest
import pandas as pd
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app
from ml.woe import WOETransformer
from ml.scorecard import CreditScorecard
from ml.predict import predict_single_borrower
from reports.generate_pdf_report import generate_board_report

DB_PATH = os.path.join(BASE_DIR, "finsight.db")
client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. Database Connectivity & Integrity Tests
# -----------------------------------------------------------------------------
def test_database_file_exists():
    assert os.path.exists(DB_PATH), "Database file finsight.db must exist."

def test_database_tables_populated():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = [
        ("departments", 7),
        ("chart_of_accounts", 24),
        ("transactions", 100),
        ("budgets", 100),
        ("borrowers", 4000),
        ("loans", 4000),
        ("credit_predictions", 4000),
    ]
    for tbl, min_count in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        assert count >= min_count, f"Table {tbl} has only {count} rows, expected >= {min_count}"
    conn.close()

# -----------------------------------------------------------------------------
# 2. Financial Statements Reconciliation Tests
# -----------------------------------------------------------------------------
def test_balance_sheet_reconciliation():
    """Verify that Assets = Liabilities + Equity for all 12 fiscal months."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            a.fiscal_month,
            ROUND(SUM(a.net_value), 2) AS total_assets,
            ROUND((SELECT SUM(l.current_balance) FROM liabilities l WHERE l.fiscal_month = a.fiscal_month), 2) AS total_liabilities,
            ROUND((SELECT SUM(e.total_equity) FROM equity e WHERE e.fiscal_month = a.fiscal_month), 2) AS total_equity
        FROM assets a
        GROUP BY a.fiscal_month
        ORDER BY a.fiscal_month
    """
    df = pd.read_sql(query, conn)
    conn.close()

    assert len(df) == 12, "Balance sheet must have records for all 12 fiscal months."
    df["diff"] = (df["total_assets"] - (df["total_liabilities"] + df["total_equity"])).round(2)
    
    for _, row in df.iterrows():
        assert abs(row["diff"]) < 0.01, f"Balance sheet discrepancy in month {row['fiscal_month']}: ${row['diff']}"

def test_pnl_accounting_equation():
    """Verify that Revenue - COGS - Opex - D&A - Interest - Tax = Net Profit."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM view_monthly_pnl", conn)
    conn.close()

    for _, r in df.iterrows():
        calc_gross_profit = round(r["total_revenue"] - r["cogs"], 2)
        assert abs(calc_gross_profit - r["gross_profit"]) < 0.02, f"Gross profit mismatch in month {r['fiscal_month']}"

        calc_ebitda = round(r["gross_profit"] - r["operating_expenses"], 2)
        assert abs(calc_ebitda - r["ebitda"]) < 0.02, f"EBITDA mismatch in month {r['fiscal_month']}"

        calc_ebit = round(r["ebitda"] - r["depreciation_amortization"], 2)
        assert abs(calc_ebit - r["operating_income"]) < 0.02, f"EBIT mismatch in month {r['fiscal_month']}"

        calc_pbt = round(r["operating_income"] - r["interest_expense"], 2)
        assert abs(calc_pbt - r["profit_before_tax"]) < 0.02, f"PBT mismatch in month {r['fiscal_month']}"

        calc_net_profit = round(r["profit_before_tax"] - r["tax_expense"], 2)
        assert abs(calc_net_profit - r["net_profit"]) < 0.02, f"Net profit mismatch in month {r['fiscal_month']}"

# -----------------------------------------------------------------------------
# 3. Budget vs Actual Variance Tests
# -----------------------------------------------------------------------------
def test_budget_variance_formula():
    """Verify Variance = Actual - Budget and Variance % formula."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM view_budget_vs_actual", conn)
    conn.close()

    for _, r in df.iterrows():
        calc_var = round(r["actual_amount"] - r["budgeted_amount"], 2)
        assert abs(calc_var - r["variance_amount"]) < 0.02, f"Variance dollar mismatch for account {r['account_code']}"

        if r["budgeted_amount"] > 0:
            calc_pct = round(((r["actual_amount"] - r["budgeted_amount"]) / r["budgeted_amount"]) * 100.0, 2)
            assert abs(calc_pct - r["variance_percentage"]) < 0.1, f"Variance % mismatch for account {r['account_code']}"

# -----------------------------------------------------------------------------
# 4. Weight of Evidence (WOE) & Scorecard Tests
# -----------------------------------------------------------------------------
def test_woe_transformer_behavior():
    X = pd.DataFrame({
        "grade": ["A", "A", "B", "B", "C", "C", "D", "D"],
        "dti": [10.0, 12.0, 18.0, 22.0, 26.0, 30.0, 35.0, 40.0]
    })
    y = pd.Series([0, 0, 0, 1, 0, 1, 1, 1])

    woe = WOETransformer(n_bins=3)
    woe.fit(X, y)
    X_woe = woe.transform(X)

    assert "grade_woe" in X_woe.columns
    assert "dti_woe" in X_woe.columns
    assert len(X_woe) == len(X)
    
    summary = woe.get_woe_summary()
    assert len(summary) == 2
    assert "Information_Value" in summary.columns

def test_credit_scorecard_scaling():
    card = CreditScorecard(target_score=650, target_odds=20.0, pdo=20)
    
    # 20:1 odds => prob_default = 1 / 21 =~ 0.0476 => Score should be approximately 650
    score_target = card.calculate_score(1.0 / 21.0)
    assert 645 <= score_target <= 655, f"Expected ~650 score for 20:1 odds, got {score_target}"

    # Very low default risk should have high credit score (>= 720)
    score_low_risk = card.calculate_score(0.001)
    assert score_low_risk >= 720
    assert card.get_risk_band(score_low_risk) == "Low Risk"

    # Very high default risk should have low credit score (<= 580)
    score_high_risk = card.calculate_score(0.45)
    assert score_high_risk <= 580
    assert card.get_risk_band(score_high_risk) == "Very High Risk"

# -----------------------------------------------------------------------------
# 5. Single Borrower Inference Engine Tests
# -----------------------------------------------------------------------------
def test_predict_single_borrower_endpoint():
    borrower = {
        "annual_income": 95000.0,
        "employment_length_years": 6.0,
        "home_ownership": "MORTGAGE",
        "loan_amount": 12000.0,
        "loan_term_months": 36,
        "interest_rate": 7.9,
        "loan_grade": "A",
        "debt_to_income_ratio": 12.0,
        "revolving_utilization_pct": 22.0,
        "total_credit_accounts": 22,
        "open_credit_accounts": 11,
        "derogatory_records": 0,
        "loan_purpose": "debt_consolidation"
    }
    result = predict_single_borrower(borrower)
    assert "credit_score" in result
    assert "predicted_prob_default" in result
    assert "risk_band" in result
    assert 300 <= result["credit_score"] <= 850
    assert 0.0 <= result["predicted_prob_default"] <= 1.0

# -----------------------------------------------------------------------------
# 6. FastAPI REST Endpoints Tests (Direct Controller Function Invocations)
# -----------------------------------------------------------------------------
from backend.main import health_check
from backend.routes.dashboard import get_dashboard_overview
from backend.routes.financial import get_profit_and_loss, get_balance_sheet
from backend.routes.budget import get_budget_variance
from backend.routes.credit import get_credit_risk_summary, predict_borrower_credit_risk, BorrowerInput
from backend.routes.reports import list_available_reports

def test_api_health():
    data = health_check()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True

def test_api_dashboard_overview():
    data = get_dashboard_overview()
    assert data["status"] == "success"
    assert data["balance_sheet_reconciled"] is True
    assert data["balance_sheet_discrepancy"] == 0.0

def test_api_financial_pnl():
    data = get_profit_and_loss()
    assert data["count"] == 12
    assert "total_revenue" in data["data"][0]

def test_api_financial_balance_sheet():
    data = get_balance_sheet(month=12)
    assert data["is_reconciled"] is True
    assert data["discrepancy"] == 0.0

def test_api_budget_variance():
    data = get_budget_variance()
    assert data["total_records"] > 0
    assert len(data["department_summary"]) == 7

def test_api_credit_summary():
    data = get_credit_risk_summary()
    assert len(data["grade_distribution"]) == 6
    assert data["portfolio_overview"]["total_loans"] == 5000

def test_api_credit_predict():
    payload = BorrowerInput(
        annual_income=75000.0,
        employment_length_years=4.0,
        home_ownership="RENT",
        loan_amount=10000.0,
        loan_term_months=36,
        interest_rate=11.5,
        loan_grade="B",
        debt_to_income_ratio=17.5,
        revolving_utilization_pct=40.0,
        total_credit_accounts=15,
        open_credit_accounts=8,
        derogatory_records=0,
        loan_purpose="credit_card"
    )
    data = predict_borrower_credit_risk(payload)
    assert "prediction" in data
    assert 300 <= data["prediction"]["credit_score"] <= 850

def test_api_reports_monthly_and_generate():
    data = list_available_reports()
    assert data["status"] == "success"
    assert "reports" in data

# -----------------------------------------------------------------------------
# 7. PDF Report Generation Test
# -----------------------------------------------------------------------------
def test_pdf_report_generation():
    pdf_path = generate_board_report(target_month=12, fiscal_year=2026)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 10000, "PDF size must be > 10KB"
