# FinSight – System Architecture & Technical Design

## 1. System Overview

**FinSight** is an end-to-end Financial Intelligence and Credit Risk Analytics platform engineered to automate corporate financial statement analysis, budget deviation monitoring, machine learning credit default modeling, and executive board reporting.

```mermaid
flowchart TD
    subgraph DataSources["Data Sources & Ingestion"]
        DS1["Raw Ledger Data<br/>(Double-Entry ERP Transactions)"]
        DS2["Lending Club Credit Data<br/>(5,000 Borrower Loan Files)"]
        DS3["Department Budgets<br/>(132 Monthly Allocations)"]
    end

    subgraph StorageEngine["Relational Storage Layer"]
        DB["SQLite Embedded Engine (finsight.db)<br/>& PostgreSQL Production DDL"]
        V1["view_monthly_pnl"]
        V2["view_budget_vs_actual"]
        V3["view_credit_risk_summary"]
        DB --> V1
        DB --> V2
        DB --> V3
    end

    subgraph AnalyticsML["Analytical & Machine Learning Core"]
        P1["SQL Financial Queries<br/>(MoM Growth, CTEs, Window Funcs)"]
        P2["Excel Power Pivot Engine<br/>(financial_model.xlsx + DAX)"]
        P3["Credit Risk ML Pipeline<br/>(WOE Transformer + Logistic Regression)"]
        P4["Basel II / FICO Scorecard<br/>(PDO Scaling: 300 - 850)"]
    end

    subgraph DeliveryUI["Demonstration & Reporting Layer"]
        API["FastAPI REST Backend<br/>(Port 8000 / Modern Async)"]
        SPA["FinSight Enterprise Web UI<br/>(Tailwind CSS, Chart.js, Recharts)"]
        REP["Automated PDF Board Report<br/>(ReportLab Vector Engine)"]
        PA["Power Automate Cloud Workflow<br/>(Monthly Schedule & Email Distribution)"]
        QLIK["Qlik Sense Enterprise BI<br/>(Load Scripts & 4 Master Dashboards)"]
    end

    DataSources --> StorageEngine
    StorageEngine --> AnalyticsML
    AnalyticsML --> DeliveryUI
    API --> SPA
    API --> REP
```

---

## 2. Component Architecture

### A. Data Ingestion & Storage Architecture
- **Normalized Relational Schema**: 13 tables enforcing primary/foreign key referential integrity.
- **Strict Double-Entry Guarantee**: Every transaction balances debit and credit allocations. Cash acts as the reconciling balance ensuring:
$$\text{Total Assets} = \text{Total Liabilities} + \text{Total Equity} \quad (\Delta = \$0.00)$$
- **Portability**: Dual-engine DDL supporting both zero-dependency embedded **SQLite** (bundled in repository) and enterprise **PostgreSQL 16+**.

### B. Analytical & Machine Learning Core
- **Financial Calculation Engine**: Computes GAAP P&L statement items:
$$\text{Gross Profit} = \text{Revenue} - \text{COGS}$$
$$\text{EBITDA} = \text{Gross Profit} - \text{Operating Expenses}$$
$$\text{Operating Income (EBIT)} = \text{EBITDA} - \text{Depreciation \& Amortization}$$
$$\text{Profit Before Tax (EBT)} = \text{EBIT} - \text{Interest Expense}$$
$$\text{Net Profit} = \text{EBT} - \text{Income Tax Provision}$$
- **Weight of Evidence (WOE) Engine**: Quantile binning that linearizes relationships with the default target and isolates Information Value (IV).
- **Credit Scorecard Engine**: Scales logistic regression probabilities to industry standard credit scores:
$$\text{Score} = \text{Offset} + \left(\frac{\text{PDO}}{\ln(2)}\right) \times \ln\left(\frac{1 - P(\text{Default})}{P(\text{Default})}\right)$$

### C. Application & Delivery Layer
- **FastAPI REST API**: High-performance asynchronous microservice providing endpoints for financial KPIs, budget variance, borrower inference, and PDF report compilation.
- **Enterprise Web UI**: Responsive, Bloomberg-inspired demonstration interface with dark/light themes, interactive charts, and real-time borrower credit simulator.
- **Automated Reporting**: Headless vector PDF generation engine with dynamic page numbering and executive sign-off blocks.
- **Power Automate Cloud Architecture**: Fully documented monthly cron recurrence flow orchestrating data health validation, report compilation, and Office 365 Outlook distribution.
