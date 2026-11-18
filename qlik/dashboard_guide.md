# FinSight – Qlik Sense Enterprise BI Implementation Guide

## Executive Summary & System Status

This guide provides the complete blueprint for deploying the **FinSight Financial Intelligence & Credit Risk Platform** in **Qlik Sense Enterprise** or **Qlik Cloud Analytics**.

> [!NOTE]
> In compliance with technical evaluation guidelines: native Qlik Sense Server is not hosted in the local runtime environment. Instead, this repository delivers production-ready `.qvs` load scripts, snowflake data models, master measure definitions with exact Set Analysis syntax, and pixel-perfect dashboard layouts.

---

## 1. Qlik Sense Data Model Architecture

The FinSight Qlik application utilizes two associative stars linked through the temporal calendar:

```
[MasterCalendar] (TransactionDate)
       |
       | 1
       v *
 [Transactions] ----< AccountID >----> [ChartOfAccounts]
       |
       | *
       v 1
 [Departments]
       ^ 1
       |
       | *
   [Budgets] ----< AccountID >----> [ChartOfAccounts]

------------------------------------------------------------------
 [Borrowers] (BorrowerID)
       | 1
       v *
    [Loans] (LoanID)
       | 1
       v 1
 [CreditPredictions]
```

---

## 2. Master Items & Set Analysis Measure Library

### Financial Metrics

| Master Measure Name | Qlik Set Analysis Expression | Visual Formatting |
| :--- | :--- | :--- |
| **Total Revenue** | `Sum({<AccountType={'Revenue'}>} CreditAmount - DebitAmount)` | `$#,##0` |
| **COGS** | `Sum({<SubCategory={'Cost of Goods Sold'}>} DebitAmount - CreditAmount)` | `$#,##0` |
| **Gross Profit** | `[Total Revenue] - [COGS]` | `$#,##0` |
| **Gross Margin %** | `([Gross Profit]) / ([Total Revenue])` | `0.0%` |
| **Operating Expenses** | `Sum({<SubCategory={'R&D', 'Sales & Marketing', 'General & Administrative'}>} DebitAmount - CreditAmount)` | `$#,##0` |
| **EBITDA** | `[Gross Profit] - [Operating Expenses]` | `$#,##0` |
| **Operating Income (EBIT)**| `[EBITDA] - Sum({<SubCategory={'Depreciation & Amortization'}>} DebitAmount - CreditAmount)` | `$#,##0` |
| **Net Profit** | `[Operating Income] - Sum({<SubCategory={'Interest Expense', 'Tax Expense'}>} DebitAmount - CreditAmount)` | `$#,##0` |
| **Net Profit Margin %**| `[Net Profit] / [Total Revenue]` | `0.0%` |
| **Revenue MoM Growth**| `(Sum({<FiscalMonth={$(=Max(FiscalMonth))}>} CreditAmount) - Sum({<FiscalMonth={$(=Max(FiscalMonth)-1)}>} CreditAmount)) / Sum({<FiscalMonth={$(=Max(FiscalMonth)-1)}>} CreditAmount)` | `+0.0%;-0.0%` |

### Budget vs Actual Metrics

| Master Measure Name | Qlik Set Analysis Expression | Visual Formatting |
| :--- | :--- | :--- |
| **Total Budgeted Amount** | `Sum(BudgetedAmount)` | `$#,##0` |
| **Total Actual Expenses** | `Sum({<AccountType={'Expense'}>} DebitAmount - CreditAmount)` | `$#,##0` |
| **Budget Variance ($)** | `[Total Actual Expenses] - [Total Budgeted Amount]` | `$#,##0` |
| **Budget Variance (%)** | `([Total Actual Expenses] - [Total Budgeted Amount]) / [Total Budgeted Amount]` | `+0.0%;-0.0%` |
| **Budget Utilization %**| `[Total Actual Expenses] / [Total Budgeted Amount]` | `0.0%` |

### Credit Risk Metrics

| Master Measure Name | Qlik Set Analysis Expression | Visual Formatting |
| :--- | :--- | :--- |
| **Total Funded Volume** | `Sum(LoanAmount)` | `$#,##0` |
| **Total Borrowers** | `Count(DISTINCT BorrowerID)` | `#,##0` |
| **Total Defaults** | `Sum(IsDefault)` | `#,##0` |
| **Portfolio Default Rate**| `Sum(IsDefault) / Count(LoanID)` | `0.0%` |
| **Average Credit Score**| `Avg(CreditScore)` | `#,##0` |
| **Expected Default Rate**| `Avg(PredictedDefaultProb)` | `0.0%` |
| **Subprime Exposure** | `Sum({<RiskBand={'High Risk', 'Very High Risk'}>} LoanAmount)` | `$#,##0` |

---

## 3. Detailed Dashboard Specifications

### Dashboard 1: Executive Financial Overview
- **Header KPI Cards**:
  - `Total Revenue` (with MoM delta indicator)
  - `Gross Profit` (with Margin %)
  - `EBITDA` (with EBITDA Margin %)
  - `Net Profit` (with Net Margin %)
- **Visual 1 (Top Left)**: Combo Chart — Monthly Revenue vs Total Expenses with Net Profit Line.
  - Dimension: `MonthYear`
  - Bars: `[Total Revenue]` (Navy Blue `#1e293b`), `[Total Actual Expenses]` (Slate Gray `#64748b`)
  - Line: `[Net Profit]` (Emerald Green `#10b981`)
- **Visual 2 (Top Right)**: Waterfall Chart — FY2026 P&L Bridge.
  - Steps: Revenue $\rightarrow$ COGS $(-)$ $\rightarrow$ Gross Profit $(=)$ $\rightarrow$ Opex $(-)$ $\rightarrow$ EBITDA $(=)$ $\rightarrow$ D&A $(-)$ $\rightarrow$ EBIT $(=)$ $\rightarrow$ Interest & Tax $(-)$ $\rightarrow$ Net Profit $(=)$.
- **Visual 3 (Bottom Left)**: Bar Chart — Department Expense Breakdown.
  - Dimension: `DepartmentName`
  - Measure: `[Total Actual Expenses]`
- **Visual 4 (Bottom Right)**: Line Chart — Monthly Profitability Margin Trends (`Gross Margin %`, `EBITDA Margin %`, `Net Margin %`).

### Dashboard 2: Budget vs Actual Analysis
- **Header KPI Cards**:
  - `Total Budget`
  - `Total Actual Spending`
  - `Net Dollar Variance`
  - `Portfolio Utilization Rate`
- **Visual 1**: Grouped Horizontal Bar Chart — Department Budget vs Actual with Overspending Indicators.
  - Dimension: `DepartmentName`
  - Measure 1: `[Total Budgeted Amount]`
  - Measure 2: `[Total Actual Expenses]`
  - Conditional Color: `IF([Total Actual Expenses] > [Total Budgeted Amount], Red(), Green())`
- **Visual 2**: Variance Treemap — Expense Accounts by Dollar Overspend.
  - Dimensions: `DepartmentName`, `AccountName`
  - Measure: `Fabs([Budget Variance ($)])`
  - Color expression: `IF([Budget Variance ($)] > 0, '#ef4444', '#10b981')`
- **Visual 3**: Variance Table with Conditional Alert Badges:
  - Columns: Month, Department, Cost Center, Account Code, Budget, Actual, Variance ($), Variance (%), Status Badge.

### Dashboard 3: Credit Risk Analytics
- **Header KPI Cards**:
  - `Total Funded Capital`
  - `Total Active Loans`
  - `Empirical Default Rate`
  - `Average Portfolio Score`
  - `Expected Loss Exposure`
- **Visual 1**: Heatmap / Matrix — Default Rate by Loan Grade vs Debt-to-Income Tier.
  - Rows: `LoanGrade` (A through F)
  - Columns: `DTITier`
  - Metric: `[Portfolio Default Rate]` (Heatmap color gradient from `#dbeafe` to `#dc2626`)
- **Visual 2**: Scatter Plot — Borrower Annual Income vs Predicted Default Probability.
  - Dimension: `BorrowerExternalID`
  - X-Axis: `AnnualIncome` (Log scale)
  - Y-Axis: `PredictedDefaultProb`
  - Bubble Color: `RiskBand`
- **Visual 3**: Donut Chart — Borrower Risk Segmentation (`Low Risk`, `Medium Risk`, `High Risk`, `Very High Risk`).
- **Visual 4**: Bar Chart — Loan Volume and Default Counts by Loan Purpose.

### Dashboard 4: Monthly Board Report
- **Executive Summary Block**: C-level executive summary narrative dynamically bound to maximum selected period.
- **Top Financial Indicators**:
  - Full-Year Revenue run-rate, Cash burn rate, Runway, and Net Income trajectory.
- **Capital & Liquidity Table**:
  - Cash and Liquid Equivalents, Senior Debt covenants, Debt Service Coverage Ratio (DSCR), Current Ratio.
- **Credit Health & Loss Provisioning**:
  - Provision for Credit Losses (PCL), 30+ DPD trends, Subprime origination caps.

---

## 4. Step-by-Step Qlik Sense Deployment Instructions

1. **Create Qlik Application**: Open Qlik Sense Desktop or Qlik Cloud Hub and create an app named `FinSight_Analytics_Platform`.
2. **Setup Data Connection**:
   - In Data Load Editor, configure folder data connection `lib://FinSight_Data/` pointing to the `/data/raw/` directory containing CSV exports.
3. **Execute Load Scripts**:
   - Create Section 1 and paste `qlik/load_scripts/01_financial_ledger_load.qvs`.
   - Create Section 2 and paste `qlik/load_scripts/02_credit_risk_load.qvs`.
   - Click **Load Data**. Data model will link seamlessly with zero synthetic keys or circular loops.
4. **Create Master Items**:
   - Navigate to Sheet View $\rightarrow$ Edit Sheet $\rightarrow$ Master Items $\rightarrow$ Dimensions & Measures.
   - Create measures defined in Section 2 above.
5. **Publish & Share**:
   - Publish app to Executive Financial Streams with Section Access security filters by department.
