# FinSight – Financial & Credit Risk Metric Definitions

This document defines the mathematical formulas, accounting interpretations, and source database tables for all key performance indicators (KPIs) in the FinSight platform.

---

## 1. Income Statement (P&L) Metrics

### Total Revenue
- **Definition**: The gross recognized revenue from all corporate operational revenue streams, including Enterprise SaaS subscriptions, professional consulting services, and platform API usage fees.
- **Formula**:
$$\text{Total Revenue} = \sum (\text{Credit Amount} - \text{Debit Amount}) \quad \forall \text{ accounts where sub\_category} = \text{'Revenue'}$$
- **Source Table**: `transactions` JOIN `chart_of_accounts`

### Cost of Goods Sold (COGS)
- **Definition**: Direct costs attributable to platform service delivery and hosting infrastructure (e.g. AWS/Azure hosting compute, Kubernetes clusters, and implementation labor).
- **Formula**:
$$\text{COGS} = \sum (\text{Debit Amount} - \text{Credit Amount}) \quad \forall \text{ accounts where sub\_category} = \text{'Cost of Goods Sold'}$$
- **Source Table**: `transactions` JOIN `chart_of_accounts`

### Gross Profit & Gross Margin
- **Definition**: Net financial value generated after deducting direct product and delivery costs from top-line revenue.
- **Formulas**:
$$\text{Gross Profit} = \text{Total Revenue} - \text{COGS}$$
$$\text{Gross Margin \%} = \left(\frac{\text{Gross Profit}}{\text{Total Revenue}}\right) \times 100$$

### Operating Expenses (Opex)
- **Definition**: Operational overhead expenses required to maintain business operations, excluding COGS, D&A, interest, and taxes. Comprises R&D engineering, Sales & Marketing campaigns, and General & Administrative (G&A) overhead.
- **Formula**:
$$\text{Opex} = \sum (\text{Debit Amount} - \text{Credit Amount}) \quad \forall \text{ sub\_categories} \in \{\text{'R\&D'}, \text{'Sales \& Marketing'}, \text{'General \& Administrative'}\}$$

### EBITDA (Earnings Before Interest, Taxes, Depreciation & Amortization)
- **Definition**: A standard corporate measure of core operating cash profitability before the impact of capital structure and non-cash accounting charges.
- **Formula**:
$$\text{EBITDA} = \text{Gross Profit} - \text{Operating Expenses}$$
$$\text{EBITDA Margin \%} = \left(\frac{\text{EBITDA}}{\text{Total Revenue}}\right) \times 100$$

### Operating Income (EBIT)
- **Definition**: Earnings generated purely from operations after accounting for asset wear-and-tear (depreciation) and intangible write-offs (amortization).
- **Formula**:
$$\text{Operating Income} = \text{EBITDA} - \text{Depreciation \& Amortization}$$

### Net Profit (Net Income) & Net Profit Margin
- **Definition**: The ultimate bottom-line earnings retained by the company after deducting interest expenses and corporate income taxes (21% statutory rate).
- **Formulas**:
$$\text{Profit Before Tax (EBT)} = \text{Operating Income} - \text{Interest Expense}$$
$$\text{Net Profit} = \text{EBT} - \text{Income Tax Provision}$$
$$\text{Net Profit Margin \%} = \left(\frac{\text{Net Profit}}{\text{Total Revenue}}\right) \times 100$$

---

## 2. Balance Sheet & Reconciliation Metrics

### Fundamental Balance Sheet Identity
- **Accounting Principle**: The fundamental equation of double-entry bookkeeping:
$$\text{Total Assets} = \text{Total Liabilities} + \text{Total Equity}$$
- **Discrepancy Formula**:
$$\text{Discrepancy} = \text{Total Assets} - (\text{Total Liabilities} + \text{Total Equity})$$
- **Reconciliation Criterion**:
$$\text{Status} = \begin{cases} \text{'RECONCILED'}, & \text{if } |\text{Discrepancy}| < \$0.01 \\ \text{'DISCREPANCY DETECTED'}, & \text{otherwise} \end{cases}$$
- **Source Tables**: `assets`, `liabilities`, `equity`

---

## 3. Budget vs Actual Variance Metrics

### Budget Variance ($)
- **Definition**: The numerical difference between actual financial spending and the approved budget allocation.
- **Formula**:
$$\text{Variance Amount} = \text{Actual Amount} - \text{Budgeted Amount}$$
- **Interpretation**:
  - For Expenses: Positive variance represents **Overspending** (Unfavorable), negative represents **Savings** (Favorable).
  - For Revenue: Positive variance represents **Exceeding Target** (Favorable), negative represents **Underperformance** (Unfavorable).

### Budget Variance (%)
- **Definition**: The percentage deviation of actual spending relative to the approved budget.
- **Formula**:
$$\text{Variance \%} = \begin{cases} 0.00, & \text{if } \text{Budgeted Amount} = 0 \\ \left(\frac{\text{Actual Amount} - \text{Budgeted Amount}}{\text{Budgeted Amount}}\right) \times 100, & \text{otherwise} \end{cases}$$

---

## 4. Credit Risk Intelligence & Machine Learning Metrics

### Empirical Default Rate
- **Definition**: Proportion of loans in the portfolio that resulted in terminal charge-off or default.
- **Formula**:
$$\text{Default Rate \%} = \left(\frac{\sum \text{is\_default}}{\text{Total Loans Count}}\right) \times 100$$

### Weight of Evidence (WOE)
- **Definition**: Log-ratio of the proportion of non-defaulting ("Good") borrowers to defaulting ("Bad") borrowers within a given feature bin $i$.
- **Formula**:
$$\text{WOE}_i = \ln\left(\frac{\text{Dist Good}_i}{\text{Dist Bad}_i}\right) = \ln\left(\frac{\text{Good}_i / \text{Total Good}}{\text{Bad}_i / \text{Total Bad}}\right)$$

### Information Value (IV)
- **Definition**: Total predictive power of an explanatory variable across all its discrete bins:
$$\text{IV} = \sum_{i=1}^{k} (\text{Dist Good}_i - \text{Dist Bad}_i) \times \text{WOE}_i$$

### FICO-Scaled Credit Score
- **Formula**:
$$\text{Score} = \text{Offset} + \left(\frac{\text{PDO}}{\ln(2)}\right) \times \ln\left(\frac{1 - P(\text{Default})}{P(\text{Default})}\right)$$
- **Calibrated Parameters**: Target Score = 650 at 20:1 Odds, Points to Double the Odds ($\text{PDO}$) = 20. Bounds: $[300, 850]$.
