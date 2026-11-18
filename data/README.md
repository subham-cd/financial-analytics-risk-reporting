# FinSight – Dataset Documentation & Data Lineage

This directory archives raw and processed datasets powering the FinSight platform.

---

## 1. Datasets Summary

| Dataset File | Records | Source / Methodology | Description |
| :--- | :---: | :--- | :--- |
| **`transactions_ledger_raw.csv`** | 144 | Synthetic Double-Entry Generator | 12-month corporate financial transaction ledger with debit/credit balance. |
| **`budgets_raw.csv`** | 132 | Approved Financial Plan | Monthly approved departmental budget line items. |
| **`borrowers_raw.csv`** | 5,000 | Lending Club Statistical Distributions | Borrower profiles (income, employment, home ownership, geography). |
| **`loans_raw.csv`** | 5,000 | Lending Club Statistical Distributions | Credit attributes (loan amounts, interest rates, DTI, revolving utilization, defaults). |

---

## 2. Dataset Strategy & Realism

### Dataset A: Corporate Double-Entry Financial Ledger
- **Accounting Standard:** US GAAP compliant chart of accounts.
- **Reconciliation Proof:** Every transaction follows double-entry debit/credit mechanics.
- **Balance Sheet Identity:** Cash balances reconcile to ensure:
$$\text{Total Assets} = \text{Total Liabilities} + \text{Total Equity} \quad (\Delta = \$0.00)$$

### Dataset B: Credit Risk & Default Portfolio
- **Inspiration:** Lending Club Loan Dataset (Public Domain / CC0).
- **Target Variable Definition (`is_default`):**
  - `0` = Fully Paid / Performing borrower.
  - `1` = Default / 120+ Days Past Due / Charged-Off borrower.
- **Empirical Portfolio Default Rate:** **16.38%** (819 defaults out of 5,000 total loans).
- **Monotonic Grade Scaling:**
  - Grade A: 2.24% default rate
  - Grade B: 4.48% default rate
  - Grade C: 13.60% default rate
  - Grade D: 35.38% default rate
  - Grade E: 52.44% default rate
  - Grade F: 73.29% default rate

---

## 3. Data Reproduction

To regenerate the raw datasets and refresh the SQLite database:
```bash
python database/generate_data.py
```
This script rebuilds `finsight.db` and updates the CSV archives in `data/raw/`.
