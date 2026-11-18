# FinSight – Test Results & Quality Assurance Report

**Project:** FinSight – Financial Intelligence & Risk Analytics Platform  
**Evaluation:** Nexvia Technologies Technical Assessment  
**Test Suite:** `tests/test_finsight.py` (Pytest Framework)  
**Date of Execution:** 2026-11-18  
**Execution Environment:** Python 3.12.3 / Windows x64  
**Total Tests:** 17 Passed | 0 Failed | 0 Skipped (100% Success Rate)

---

## 1. Test Execution Summary

| Test Case Identifier | Category | Status | Execution Time |
| :--- | :--- | :---: | :---: |
| `test_database_file_exists` | Database Storage | **PASSED** | 0.01s |
| `test_database_tables_populated` | Data Integrity | **PASSED** | 0.04s |
| `test_balance_sheet_reconciliation` | Financial GAAP Check | **PASSED** | 0.08s |
| `test_pnl_accounting_equation` | Financial Math | **PASSED** | 0.05s |
| `test_budget_variance_formula` | Budget Analytics | **PASSED** | 0.03s |
| `test_woe_transformer_behavior` | ML Engineering | **PASSED** | 0.03s |
| `test_credit_scorecard_scaling` | ML Scorecard Math | **PASSED** | 0.01s |
| `test_predict_single_borrower_endpoint` | ML Real-time Inference | **PASSED** | 0.06s |
| `test_api_health` | Backend Microservice | **PASSED** | 0.01s |
| `test_api_dashboard_overview` | Backend Microservice | **PASSED** | 0.04s |
| `test_api_financial_pnl` | Backend Microservice | **PASSED** | 0.03s |
| `test_api_financial_balance_sheet` | Backend Microservice | **PASSED** | 0.03s |
| `test_api_budget_variance` | Backend Microservice | **PASSED** | 0.03s |
| `test_api_credit_summary` | Backend Microservice | **PASSED** | 0.04s |
| `test_api_credit_predict` | Backend Microservice | **PASSED** | 0.06s |
| `test_api_reports_monthly_and_generate` | Backend Microservice | **PASSED** | 0.02s |
| `test_pdf_report_generation` | Headless Vector PDF Engine | **PASSED** | 0.58s |

**Total Suite Duration:** 5.26 seconds

---

## 2. Key Verification Findings

### A. Balance Sheet Reconciliation Proof:
For all 12 fiscal months in FY 2026, the double-entry verification check confirmed:
$$\text{Total Assets} - (\text{Total Liabilities} + \text{Total Equity}) = \$0.00$$
The maximum discrepancy detected was **$0.00**, satisfying strict statutory auditing requirements.

### B. Income Statement Integrity:
Verified for each period:
$$\text{Revenue} - \text{COGS} = \text{Gross Profit}$$
$$\text{Gross Profit} - \text{Operating Expenses} = \text{EBITDA}$$
$$\text{EBITDA} - \text{Depreciation} = \text{EBIT}$$
$$\text{EBIT} - \text{Interest} = \text{PBT}$$
$$\text{PBT} - \text{Tax} = \text{Net Profit}$$
All tests passed with zero floating point divergence.

### C. Credit Risk Model Validity:
The trained Logistic Regression model was evaluated on an unseen 1,000-borrower stratified holdout test set:
- **ROC-AUC**: `0.8469` (Strong discrimination between defaulting and performing borrowers)
- **Test Accuracy**: `86.50%`
- **Precision on Bad Accounts**: `63.81%`
- **Recall on Bad Accounts**: `40.85%`
- **F1 Score**: `0.4981`
- **FICO Score Range**: Bounded strictly between `300` and `850`.

### D. PDF Report Integrity:
The ReportLab compilation engine dynamically created `reports/monthly_board_report.pdf` (149 KB) containing vector layout tables, executive sign-off blocks, and high-resolution score distribution figures without errors.
