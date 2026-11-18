"""
FinSight Platform - Executive Dashboard Overview API Routes
"""

from fastapi import APIRouter
from backend.app.database import execute_query, execute_one

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/overview")
def get_dashboard_overview():
    """Returns top-level business intelligence metrics, full-year totals, and reconciliation status."""
    
    # 1. Full-Year Financials
    pnl_fy = execute_one("""
        SELECT 
            ROUND(SUM(total_revenue), 2) AS total_revenue,
            ROUND(SUM(cogs), 2) AS total_cogs,
            ROUND(SUM(gross_profit), 2) AS gross_profit,
            ROUND(SUM(operating_expenses), 2) AS operating_expenses,
            ROUND(SUM(ebitda), 2) AS ebitda,
            ROUND(SUM(net_profit), 2) AS net_profit,
            ROUND((SUM(gross_profit) / NULLIF(SUM(total_revenue), 0)) * 100.0, 2) AS gross_margin_pct,
            ROUND((SUM(ebitda) / NULLIF(SUM(total_revenue), 0)) * 100.0, 2) AS ebitda_margin_pct,
            ROUND((SUM(net_profit) / NULLIF(SUM(total_revenue), 0)) * 100.0, 2) AS net_profit_margin_pct
        FROM view_monthly_pnl
    """)

    # 2. Latest Month Performance (M12)
    latest_m = execute_one("""
        SELECT 
            fiscal_month,
            total_revenue,
            gross_profit,
            ebitda,
            net_profit
        FROM view_monthly_pnl
        ORDER BY fiscal_month DESC LIMIT 1
    """)

    # 3. Budget vs Actual Summary
    budget_summary = execute_one("""
        SELECT 
            ROUND(SUM(budgeted_amount), 2) AS total_budget,
            ROUND(SUM(actual_amount), 2) AS total_actual,
            ROUND(SUM(actual_amount) - SUM(budgeted_amount), 2) AS variance_amount,
            ROUND(((SUM(actual_amount) - SUM(budgeted_amount)) / NULLIF(SUM(budgeted_amount), 0)) * 100.0, 2) AS variance_pct
        FROM view_budget_vs_actual
        WHERE account_type = 'Expense'
    """)

    # 4. Credit Portfolio High-Level
    credit_summary = execute_one("""
        SELECT 
            COUNT(loan_id) AS total_loans,
            ROUND(SUM(loan_amount), 2) AS total_funded_volume,
            ROUND(AVG(loan_amount), 2) AS avg_loan_size,
            ROUND(AVG(debt_to_income_ratio), 2) AS avg_dti,
            SUM(is_default) AS total_defaults,
            ROUND((SUM(is_default) * 1.0 / COUNT(loan_id)) * 100.0, 2) AS default_rate_pct
        FROM loans
    """)

    # 5. Scorecard Distribution
    scorecard_summary = execute_one("""
        SELECT 
            ROUND(AVG(credit_score), 0) AS avg_credit_score,
            ROUND(AVG(predicted_prob_default) * 100.0, 2) AS avg_predicted_default_prob_pct
        FROM credit_predictions
    """)

    # 6. Monthly Financial Trends
    monthly_trends = execute_query("""
        SELECT 
            fiscal_month,
            total_revenue,
            cogs,
            gross_profit,
            operating_expenses,
            ebitda,
            net_profit
        FROM view_monthly_pnl
        ORDER BY fiscal_month
    """)

    # 7. Balance Sheet Reconciliation Check
    bs_recon = execute_query("""
        SELECT 
            a.fiscal_month,
            ROUND(SUM(a.net_value), 2) AS total_assets,
            ROUND((SELECT SUM(l.current_balance) FROM liabilities l WHERE l.fiscal_month = a.fiscal_month), 2) AS total_liabilities,
            ROUND((SELECT SUM(e.total_equity) FROM equity e WHERE e.fiscal_month = a.fiscal_month), 2) AS total_equity
        FROM assets a
        GROUP BY a.fiscal_month
        ORDER BY a.fiscal_month DESC LIMIT 1
    """)
    latest_bs = bs_recon[0] if bs_recon else {"total_assets": 0, "total_liabilities": 0, "total_equity": 0}
    bs_diff = round(latest_bs["total_assets"] - (latest_bs["total_liabilities"] + latest_bs["total_equity"]), 2)

    return {
        "status": "success",
        "reporting_period": "FY 2026",
        "financial_kpis": pnl_fy,
        "latest_month": latest_m,
        "budget_variance": budget_summary,
        "credit_portfolio": {**credit_summary, **scorecard_summary},
        "monthly_trends": monthly_trends,
        "balance_sheet_reconciled": abs(bs_diff) < 0.01,
        "balance_sheet_discrepancy": bs_diff
    }
