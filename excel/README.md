# FinSight – Financial Modeling & Power Pivot Documentation

## Overview

The `financial_model.xlsx` workbook provides an enterprise-grade financial modeling platform built according to GAAP accounting principles. It bridges the relational database transaction engine with executive-ready spreadsheet analytics, supporting dynamic Excel formulas and Microsoft Power Pivot data modeling.

---

## 1. Workbook Structure & Worksheets

| Worksheet Name | Primary Purpose | Key Formulas & Methodologies |
| :--- | :--- | :--- |
| **`P&L Statement`** | 12-Month Profit & Loss Statement | Gross Profit (`Revenue - COGS`), EBITDA (`Gross Profit - Opex`), Operating Income (`EBITDA - D&A`), Net Profit (`EBT - Tax`), and Profit Margin ratios. |
| **`Balance Sheet`** | Reconciled Balance Sheet | Asset aggregations (Cash, AR, Inventory, Net Fixed Assets, Other Assets), Liability aggregations (AP, Short-Term Debt, Long-Term Debt, Other Liabilities), and Equity. Includes automated reconciliation check row (`Assets - (Liabilities + Equity) = $0.00`). |
| **`Budget vs Actual`** | Variance Analysis & Monitoring | Granular department-level and account-level variance analysis (`Actual - Budget`) and variance percentage (`((Actual - Budget) / Budget) * 100`). Uses conditional formatting for overspending alerts. |
| **`Power Pivot & DAX`** | Technical Data Model Architecture | Table schema relationships, foreign key definitions, and production DAX measures for Power Pivot and Power BI data models. |

---

## 2. Power Pivot Data Model Architecture

The data model follows an analytical Star / Snowflake schema:

```
                      +-------------------+
                      |   ChartOfAccounts |
                      |   (Account_ID)    |
                      +---------+---------+
                                | 1
                                |
                                | *
+-----------------+   *       +---+---------------+       *   +-----------------+
|   Departments   |<--------->|   Transactions    |<--------->|     Budgets     |
| (Department_ID) | 1         | (Transaction_ID)  |         1 | (Department_ID, |
+-----------------+           +-------------------+           |   Account_ID)   |
                                                              +-----------------+
```

### Table Relationships:
1. `Transactions[account_id]` (Many) to `ChartOfAccounts[account_id]` (One)
2. `Transactions[department_id]` (Many) to `Departments[department_id]` (One)
3. `Budgets[account_id]` (Many) to `ChartOfAccounts[account_id]` (One)
4. `Budgets[department_id]` (Many) to `Departments[department_id]` (One)

---

## 3. Production DAX Measure Library

These DAX formulas can be copied directly into Excel Power Pivot or Microsoft Power BI:

### Financial Performance Measures

```dax
// Total Top-line Revenue
[Total Revenue] := 
SUM(Transactions[credit_amount]) - SUM(Transactions[debit_amount])

// Cost of Goods Sold
[COGS] := 
CALCULATE(
    SUM(Transactions[debit_amount]) - SUM(Transactions[credit_amount]),
    ChartOfAccounts[sub_category] = "Cost of Goods Sold"
)

// Gross Profit
[Gross Profit] := [Total Revenue] - [COGS]

// Gross Margin Percentage
[Gross Margin %] := DIVIDE([Gross Profit], [Total Revenue], 0)

// Operating Expenses (Excluding D&A)
[Operating Expenses] := 
CALCULATE(
    SUM(Transactions[debit_amount]) - SUM(Transactions[credit_amount]),
    ChartOfAccounts[sub_category] IN {"R&D", "Sales & Marketing", "General & Administrative"}
)

// EBITDA
[EBITDA] := [Gross Profit] - [Operating Expenses]

// Operating Income (EBIT)
[Operating Income] := 
[EBITDA] - CALCULATE(
    SUM(Transactions[debit_amount]) - SUM(Transactions[credit_amount]),
    ChartOfAccounts[sub_category] = "Depreciation & Amortization"
)

// Net Profit
[Net Profit] := 
[Operating Income] - CALCULATE(
    SUM(Transactions[debit_amount]) - SUM(Transactions[credit_amount]),
    ChartOfAccounts[sub_category] IN {"Interest Expense", "Tax Expense"}
)

// Net Profit Margin
[Net Profit Margin %] := DIVIDE([Net Profit], [Total Revenue], 0)
```

### Budget Variance Measures

```dax
// Total Approved Budget
[Total Budget] := SUM(Budgets[budgeted_amount])

// Budget Variance ($)
[Budget Variance] := [Operating Expenses] - [Total Budget]

// Variance Percentage (%)
[Variance %] := DIVIDE([Budget Variance], [Total Budget], 0)

// Budget Status Flag
[Budget Status] := 
IF([Budget Variance] > 0, "Over Budget", "Within Budget")
```

---

## 4. Financial Reconciliation Verification

In `Balance Sheet`, cell formula in Row 26 verifies:
$$\text{Reconciliation Check} = \text{Total Assets} - (\text{Total Liabilities} + \text{Total Equity}) = \$0.00$$

All 12 fiscal months evaluate to `$0.00`, proving strict adherence to double-entry bookkeeping.
