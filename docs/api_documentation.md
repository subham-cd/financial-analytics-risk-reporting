# FinSight – REST API Specification

The FinSight backend is powered by **FastAPI**, exposing high-performance RESTful JSON endpoints. Interactive Swagger documentation is accessible at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

---

## Base URL
```
http://127.0.0.1:8000
```

---

## 1. System Health

### `GET /api/health`
Checks backend microservice health and relational database connectivity.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "platform": "FinSight Financial Intelligence",
  "version": "2.0.0",
  "database_connected": true
}
```

---

## 2. Executive Dashboard Overview

### `GET /api/dashboard/overview`
Retrieves aggregated top-line financial KPIs, latest monthly metrics, credit portfolio summary, and balance sheet reconciliation status.

**Response (200 OK):**
```json
{
  "status": "success",
  "reporting_period": "FY 2026",
  "financial_kpis": {
    "total_revenue": 26867746.42,
    "total_cogs": 5910874.15,
    "gross_profit": 20956872.27,
    "operating_expenses": 14787948.33,
    "ebitda": 6168923.94,
    "net_profit": 4443689.91,
    "gross_margin_pct": 78.0,
    "ebitda_margin_pct": 22.96,
    "net_profit_margin_pct": 16.54
  },
  "balance_sheet_reconciled": true,
  "balance_sheet_discrepancy": 0.0
}
```

---

## 3. Financial Statements

### `GET /api/financial/profit-loss`
Retrieves monthly P&L records with MoM revenue growth and margin percentages.

**Query Parameters:**
- `month` *(optional, integer)*: Filter by fiscal month (1-12).

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 12,
  "data": [
    {
      "fiscal_year": 2026,
      "fiscal_month": 1,
      "total_revenue": 1912793.95,
      "cogs": 421380.25,
      "gross_profit": 1491413.7,
      "operating_expenses": 987680.74,
      "ebitda": 503732.96,
      "depreciation_amortization": 45000.0,
      "operating_income": 458732.96,
      "interest_expense": 24500.0,
      "profit_before_tax": 434232.96,
      "tax_expense": 91188.92,
      "net_profit": 343044.04,
      "gross_margin_pct": 77.97,
      "ebitda_margin_pct": 26.33,
      "net_profit_margin_pct": 17.93,
      "mom_growth_pct": 0.0
    }
  ]
}
```

### `GET /api/financial/balance-sheet`
Returns full asset, liability, and equity ledger breakdowns with reconciliation check proofs.

**Query Parameters:**
- `month` *(optional, integer, default: 12)*: Target month.

**Response (200 OK):**
```json
{
  "status": "success",
  "selected_month": 12,
  "total_assets": 22766892.33,
  "total_liabilities": 6388169.56,
  "total_equity": 16378722.77,
  "total_liabilities_and_equity": 22766892.33,
  "discrepancy": 0.0,
  "is_reconciled": true
}
```

---

## 4. Budget vs Actual Analysis

### `GET /api/budget/variance`
Retrieves department and account-level variance analysis.

**Query Parameters:**
- `month` *(optional, integer)*: Target fiscal month.
- `department` *(optional, string)*: Department code (e.g. `ENG`, `SLS`).

**Response (200 OK):**
```json
{
  "status": "success",
  "total_records": 132,
  "department_summary": [
    {
      "department_code": "ENG",
      "department_name": "Engineering & Technology",
      "total_budget": 5373549.28,
      "total_actual": 5519800.12,
      "variance_amount": 146250.84,
      "variance_percentage": 2.72,
      "overall_status": "Over Budget"
    }
  ]
}
```

---

## 5. Credit Risk & Scorecard Inference

### `GET /api/credit-risk/summary`
Retrieves credit portfolio statistics, grade distributions, and ML model performance metrics.

### `POST /api/credit-risk/predict`
Calculates real-time credit default probability and scaled FICO score for a borrower.

**Request Body (JSON):**
```json
{
  "annual_income": 85000.0,
  "employment_length_years": 5.0,
  "home_ownership": "MORTGAGE",
  "loan_amount": 15000.0,
  "loan_term_months": 36,
  "interest_rate": 10.5,
  "loan_grade": "B",
  "debt_to_income_ratio": 16.5,
  "revolving_utilization_pct": 35.0,
  "total_credit_accounts": 18,
  "open_credit_accounts": 9,
  "derogatory_records": 0,
  "loan_purpose": "debt_consolidation"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "prediction": {
    "predicted_prob_default": 0.0215,
    "predicted_prob_default_pct": 2.15,
    "credit_score": 673,
    "risk_band": "Medium Risk",
    "underwriting_recommendation": "Approve: Standard terms with standard underwriting review",
    "model_version": "v1.0.0-logistic-woe",
    "decision": "APPROVED"
  }
}
```

---

## 6. Reports Generation & Streaming

### `GET /api/reports/monthly`
Lists available generated PDF reports with file sizes and download URLs.

### `POST /api/reports/generate`
Compiles an executive vector PDF Board Report using ReportLab.

### `GET /api/reports/download/{filename}`
Streams the compiled binary PDF document directly to the client browser.
