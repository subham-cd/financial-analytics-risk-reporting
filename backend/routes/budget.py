"""
FinSight Platform - Budget vs Actual Variance Analysis API Routes
"""

from typing import Optional
from fastapi import APIRouter
from backend.app.database import execute_query

router = APIRouter(prefix="/api/budget", tags=["Budget vs Actual"])

@router.get("/variance")
def get_budget_variance(
    month: Optional[int] = None,
    department: Optional[str] = None
):
    """Returns granular budget versus actual comparisons with conditional variance indicators."""
    conditions = []
    params = []

    if month is not None and isinstance(month, int):
        conditions.append("fiscal_month = ?")
        params.append(month)
    if department is not None and isinstance(department, str):
        conditions.append("department_code = ?")
        params.append(department)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
        SELECT 
            fiscal_month,
            department_code,
            department_name,
            account_code,
            account_name,
            account_type,
            budgeted_amount,
            actual_amount,
            variance_amount,
            variance_percentage,
            budget_status
        FROM view_budget_vs_actual
        {where_clause}
        ORDER BY fiscal_month, department_code, account_code
    """
    rows = execute_query(query, tuple(params))

    # Department Level Summary
    dept_summary = execute_query(f"""
        SELECT 
            department_code,
            department_name,
            ROUND(SUM(budgeted_amount), 2) AS total_budget,
            ROUND(SUM(actual_amount), 2) AS total_actual,
            ROUND(SUM(actual_amount) - SUM(budgeted_amount), 2) AS variance_amount,
            ROUND(((SUM(actual_amount) - SUM(budgeted_amount)) / NULLIF(SUM(budgeted_amount), 0)) * 100.0, 2) AS variance_percentage,
            CASE 
                WHEN SUM(actual_amount) > SUM(budgeted_amount) THEN 'Over Budget'
                ELSE 'Within Budget'
            END AS overall_status
        FROM view_budget_vs_actual
        {where_clause}
        GROUP BY department_code, department_name
        ORDER BY total_actual DESC
    """, tuple(params))

    return {
        "status": "success",
        "total_records": len(rows),
        "department_summary": dept_summary,
        "line_items": rows
    }
