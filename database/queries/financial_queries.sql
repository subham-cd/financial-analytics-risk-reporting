-- ============================================================================
-- FinSight Platform - Advanced Financial Reporting & Analytics Queries
-- Evaluation: Nexvia Technologies Technical Assessment
-- Demonstrates: CTEs, Window Functions (LAG, OVER), Joins, Aggregations, Ratios
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Monthly Revenue, COGS, Gross Profit, and MoM Revenue Growth Rate
-- ----------------------------------------------------------------------------
WITH monthly_sales AS (
    SELECT 
        t.fiscal_year,
        t.fiscal_month,
        SUM(CASE WHEN coa.sub_category = 'Revenue' THEN t.credit_amount - t.debit_amount ELSE 0 END) AS total_revenue,
        SUM(CASE WHEN coa.sub_category = 'Cost of Goods Sold' THEN t.debit_amount - t.credit_amount ELSE 0 END) AS cogs
    FROM transactions t
    JOIN chart_of_accounts coa ON t.account_id = coa.account_id
    GROUP BY t.fiscal_year, t.fiscal_month
)
SELECT 
    fiscal_year,
    fiscal_month,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(cogs, 2) AS cogs,
    ROUND(total_revenue - cogs, 2) AS gross_profit,
    ROUND(((total_revenue - cogs) / NULLIF(total_revenue, 0)) * 100.0, 2) AS gross_margin_pct,
    LAG(total_revenue, 1) OVER (ORDER BY fiscal_year, fiscal_month) AS prev_month_revenue,
    ROUND(
        ((total_revenue - LAG(total_revenue, 1) OVER (ORDER BY fiscal_year, fiscal_month)) 
        / NULLIF(LAG(total_revenue, 1) OVER (ORDER BY fiscal_year, fiscal_month), 0)) * 100.0, 2
    ) AS mom_revenue_growth_pct
FROM monthly_sales
ORDER BY fiscal_year, fiscal_month;

-- ----------------------------------------------------------------------------
-- 2. Complete Monthly P&L with EBITDA and Operating Margin
-- ----------------------------------------------------------------------------
SELECT 
    fiscal_year,
    fiscal_month,
    total_revenue,
    cogs,
    gross_profit,
    operating_expenses,
    ebitda,
    depreciation_amortization,
    operating_income,
    interest_expense,
    profit_before_tax,
    tax_expense,
    net_profit,
    ROUND((ebitda / NULLIF(total_revenue, 0)) * 100.0, 2) AS ebitda_margin_pct,
    ROUND((net_profit / NULLIF(total_revenue, 0)) * 100.0, 2) AS net_profit_margin_pct
FROM view_monthly_pnl
ORDER BY fiscal_year, fiscal_month;

-- ----------------------------------------------------------------------------
-- 3. Department-Wise Expense Distribution and Budget Variance
-- ----------------------------------------------------------------------------
SELECT 
    d.department_code,
    d.department_name,
    d.cost_center,
    ROUND(SUM(b.budgeted_amount), 2) AS total_budgeted_expenses,
    ROUND(SUM(CASE WHEN coa.account_type = 'Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END), 2) AS total_actual_expenses,
    ROUND(SUM(CASE WHEN coa.account_type = 'Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END) - SUM(b.budgeted_amount), 2) AS expense_variance,
    ROUND(
        ((SUM(CASE WHEN coa.account_type = 'Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END) - SUM(b.budgeted_amount)) 
        / NULLIF(SUM(b.budgeted_amount), 0)) * 100.0, 2
    ) AS variance_pct,
    CASE 
        WHEN SUM(CASE WHEN coa.account_type = 'Expense' THEN t.debit_amount - t.credit_amount ELSE 0 END) > SUM(b.budgeted_amount) 
        THEN 'OVER BUDGET'
        ELSE 'FAVORABLE / UNDER BUDGET'
    END AS budget_evaluation
FROM departments d
LEFT JOIN budgets b ON d.department_id = b.department_id
LEFT JOIN chart_of_accounts coa ON b.account_id = coa.account_id AND coa.account_type = 'Expense'
LEFT JOIN transactions t ON d.department_id = t.department_id AND t.account_id = b.account_id AND t.fiscal_year = b.fiscal_year AND t.fiscal_month = b.fiscal_month
GROUP BY d.department_code, d.department_name, d.cost_center
ORDER BY total_actual_expenses DESC;

-- ----------------------------------------------------------------------------
-- 4. Balance Sheet Reconciliation Check (Assets = Liabilities + Equity)
-- ----------------------------------------------------------------------------
WITH balance_sheet_monthly AS (
    SELECT 
        a.fiscal_year,
        a.fiscal_month,
        SUM(a.net_value) AS total_assets,
        (SELECT SUM(l.current_balance) FROM liabilities l WHERE l.fiscal_year = a.fiscal_year AND l.fiscal_month = a.fiscal_month) AS total_liabilities,
        (SELECT SUM(e.total_equity) FROM equity e WHERE e.fiscal_year = a.fiscal_year AND e.fiscal_month = a.fiscal_month) AS total_equity
    FROM assets a
    GROUP BY a.fiscal_year, a.fiscal_month
)
SELECT 
    fiscal_year,
    fiscal_month,
    ROUND(total_assets, 2) AS total_assets,
    ROUND(total_liabilities, 2) AS total_liabilities,
    ROUND(total_equity, 2) AS total_equity,
    ROUND(total_liabilities + total_equity, 2) AS total_liabilities_and_equity,
    ROUND(total_assets - (total_liabilities + total_equity), 2) AS balance_sheet_discrepancy,
    CASE 
        WHEN ABS(total_assets - (total_liabilities + total_equity)) < 0.01 THEN 'RECONCILED'
        ELSE 'DISCREPANCY DETECTED'
    END AS reconciliation_status
FROM balance_sheet_monthly
ORDER BY fiscal_year, fiscal_month;

-- ----------------------------------------------------------------------------
-- 5. Credit Portfolio Risk Analysis by Loan Grade and Risk Band
-- ----------------------------------------------------------------------------
SELECT 
    l.loan_grade,
    COUNT(l.loan_id) AS total_borrowers,
    ROUND(SUM(l.loan_amount), 2) AS portfolio_exposure,
    ROUND(AVG(l.annual_income), 2) AS avg_annual_income,
    ROUND(AVG(l.debt_to_income_ratio), 2) AS avg_dti,
    ROUND(AVG(l.interest_rate), 2) AS avg_interest_rate,
    SUM(l.is_default) AS total_defaults,
    ROUND((SUM(l.is_default) * 1.0 / COUNT(l.loan_id)) * 100.0, 2) AS actual_default_rate_pct,
    ROUND(AVG(p.predicted_prob_default) * 100.0, 2) AS expected_default_rate_pct,
    ROUND(AVG(p.credit_score), 0) AS average_credit_score
FROM loans l
LEFT JOIN credit_predictions p ON l.loan_id = p.loan_id
GROUP BY l.loan_grade
ORDER BY l.loan_grade;
