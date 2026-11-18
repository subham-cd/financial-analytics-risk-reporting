"""
FinSight Platform - Financial Statement Analysis API Routes
"""

from typing import Optional
from fastapi import APIRouter
from backend.app.database import execute_query

router = APIRouter(prefix="/api/financial", tags=["Financial Statements"])

@router.get("/profit-loss")
def get_profit_and_loss(month: Optional[int] = None):
    """Returns monthly P&L records with revenue, COGS, EBITDA, and net profit margins."""
    if month is not None and isinstance(month, int):
        query = "SELECT * FROM view_monthly_pnl WHERE fiscal_month = ? ORDER BY fiscal_month"
        rows = execute_query(query, (month,))
    else:
        query = "SELECT * FROM view_monthly_pnl ORDER BY fiscal_month"
        rows = execute_query(query)

    # Calculate MoM growth and margins dynamically
    results = []
    for idx, r in enumerate(rows):
        rev = r["total_revenue"]
        gp = r["gross_profit"]
        ebitda = r["ebitda"]
        net = r["net_profit"]
        
        prev_rev = rows[idx - 1]["total_revenue"] if idx > 0 else None
        mom_growth = round(((rev - prev_rev) / prev_rev) * 100.0, 2) if prev_rev else 0.0

        item = dict(r)
        item["gross_margin_pct"] = round((gp / rev) * 100.0, 2) if rev else 0.0
        item["ebitda_margin_pct"] = round((ebitda / rev) * 100.0, 2) if rev else 0.0
        item["net_profit_margin_pct"] = round((net / rev) * 100.0, 2) if rev else 0.0
        item["mom_growth_pct"] = mom_growth
        results.append(item)

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }

@router.get("/balance-sheet")
def get_balance_sheet(month: Optional[int] = None):
    """Returns monthly Balance Sheet breakdown: Assets, Liabilities, Equity, and reconciliation checks."""
    base_m = month if (month is not None and isinstance(month, int)) else 12
    
    # Query Assets Breakdown
    assets = execute_query("""
        SELECT category, ROUND(SUM(net_value), 2) AS net_value
        FROM assets
        WHERE fiscal_month = ?
        GROUP BY category
        ORDER BY net_value DESC
    """, (base_m,))

    # Query Liabilities Breakdown
    liabilities = execute_query("""
        SELECT category, ROUND(SUM(current_balance), 2) AS current_balance
        FROM liabilities
        WHERE fiscal_month = ?
        GROUP BY category
        ORDER BY current_balance DESC
    """, (base_m,))

    # Query Equity Breakdown
    equity = execute_query("""
        SELECT share_capital, retained_earnings, total_equity
        FROM equity
        WHERE fiscal_month = ?
    """, (base_m,))

    # Verification across all 12 months
    reconciliation_trend = execute_query("""
        SELECT 
            a.fiscal_month,
            ROUND(SUM(a.net_value), 2) AS total_assets,
            ROUND((SELECT SUM(l.current_balance) FROM liabilities l WHERE l.fiscal_month = a.fiscal_month), 2) AS total_liabilities,
            ROUND((SELECT SUM(e.total_equity) FROM equity e WHERE e.fiscal_month = a.fiscal_month), 2) AS total_equity
        FROM assets a
        GROUP BY a.fiscal_month
        ORDER BY a.fiscal_month
    """)

    for r in reconciliation_trend:
        diff = round(r["total_assets"] - (r["total_liabilities"] + r["total_equity"]), 2)
        r["total_liabilities_and_equity"] = round(r["total_liabilities"] + r["total_equity"], 2)
        r["discrepancy"] = diff
        r["is_reconciled"] = abs(diff) < 0.01

    tot_assets = sum(a["net_value"] for a in assets)
    tot_liab = sum(l["current_balance"] for l in liabilities)
    tot_eq = equity[0]["total_equity"] if equity else 0.0
    discrepancy = round(tot_assets - (tot_liab + tot_eq), 2)

    return {
        "status": "success",
        "selected_month": base_m,
        "assets_breakdown": assets,
        "total_assets": round(tot_assets, 2),
        "liabilities_breakdown": liabilities,
        "total_liabilities": round(tot_liab, 2),
        "equity": equity[0] if equity else {},
        "total_equity": round(tot_eq, 2),
        "total_liabilities_and_equity": round(tot_liab + tot_eq, 2),
        "discrepancy": discrepancy,
        "is_reconciled": abs(discrepancy) < 0.01,
        "reconciliation_trend": reconciliation_trend
    }
