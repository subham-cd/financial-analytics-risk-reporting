# FinSight: Enterprise Financial Intelligence & Credit Risk Analytics Platform
## Nexvia Technologies Internship Technical Evaluation Presentation
**Presenter:** Senior Engineering Intern / Financial Analytics Lead  
**Evaluation Duration:** 10 Minutes | **Evaluation Date:** November 2026

---

## Slide 1: Title & Executive Summary
- **Project Name:** FinSight – Financial Intelligence & Risk Analytics Platform
- **Assignment:** Nexvia Technologies Technical Internship Evaluation
- **Core Mission:** Bridge corporate financial management, budget discipline, machine learning credit risk modeling, and automated executive board reporting into an integrated enterprise solution.
- **Key Deliverable:** End-to-end production software (Database, SQL, Python ML, Excel Power Pivot, Qlik Sense, Power Automate, FastAPI, Web UI).

---

## Slide 2: The Business Problem
1. **Financial Silos:** General ledger transactions, budget allocations, and borrower credit risk data exist in disconnected spreadsheets and databases.
2. **Delayed Executive Reporting:** Compiling monthly P&L and board reports takes 5-7 business days of manual spreadsheet manipulation, introducing human error.
3. **Credit Risk Blindspots:** Traditional underwriting often relies on static heuristic cutoffs rather than calibrated probability-of-default (PD) scorecards, leading to elevated default losses.
4. **Budget Slippage:** Lack of real-time variance monitoring leads to unbudgeted cost overruns across business units.

---

## Slide 3: The Proposed Solution: FinSight Platform
An end-to-end automated platform built around four pillars:
1. **GAAP Financial Statement Engine:** Reconciled double-entry ledger guaranteeing Assets = Liabilities + Equity ($\Delta = \$0.00$).
2. **Budget Variance Monitor:** Account-level variance tracking with conditional overspending alerts.
3. **Basel II / FICO Credit Scorecard:** Weight of Evidence (WOE) and Logistic Regression default prediction (ROC-AUC = 0.8469).
4. **Automated Monthly Reporting:** Scheduled Power Automate workflow and ReportLab vector PDF generation for executive leadership.

---

## Slide 4: System Architecture & Technology Stack
- **Database & Storage:** SQLite (zero-setup bundled evaluation) & PostgreSQL (enterprise DDL).
- **Analytics & Spreadsheets:** Microsoft Excel, Power Pivot, DAX measure library.
- **Machine Learning:** Scikit-learn, Pandas, NumPy, WOE transformation, FICO scorecard scaling.
- **Business Intelligence:** Qlik Sense load scripts (`.qvs`), Snowflake data model, Set Analysis.
- **Automation:** Microsoft Power Automate cloud flow, ReportLab PDF compilation.
- **Microservices & Web:** Python FastAPI, Tailwind CSS, Chart.js, Recharts.

---

## Slide 5: Module 1 & 2 – Financial Statements & Budget Analysis
- **12-Month P&L Analysis:** Full FY2026 revenue of **$26.87M**, COGS of **$5.91M** (Gross Margin 78.0%), EBITDA of **$6.17M**, and Net Profit of **$4.44M** (16.5% Net Margin).
- **Balance Sheet Reconciliation:** Assets ($22.77M) = Liabilities ($6.39M) + Equity ($16.38M) verified across all 12 fiscal months.
- **Budget Performance:** Total actual expenses tracked within **1.8%** of the approved budget plan.
- **Overspending Detection:** Real-time variance alerts highlighted mid-year R&D hiring spikes in Engineering and high sales commission pay-outs in Enterprise Sales.

---

## Slide 6: Module 3 – Credit Risk Machine Learning & Scorecard
- **Lending Club Dataset:** 5,000 borrower files with 16.4% baseline default rate.
- **Weight of Evidence (WOE):** Binned non-linear continuous attributes (DTI, utilization, income) into monotonic risk tiers.
- **Information Value (IV) Ranking:** Isolated top predictive drivers: `loan_grade` (IV: 1.66), `interest_rate` (IV: 1.45), `revolving_utilization` (IV: 1.27), and `debt_to_income` (IV: 1.08).
- **Holdout Test Set Results:**
  - **ROC-AUC:** `0.8469`
  - **Accuracy:** `86.50%`
  - **Precision:** `63.81%`
  - **Recall:** `40.85%`
  - **FICO Score Range:** Scaled from `300` to `850` (PDO = 20, Target = 650 at 20:1 odds).

---

## Slide 7: Module 4 & 5 – BI Dashboards & Power Automate Workflow
- **Qlik Sense Enterprise:**
  - 4 Master Dashboards: Executive Financial Overview, Budget vs Actual, Credit Risk Analytics, and Monthly Board Report.
  - Production Set Analysis expressions for all KPIs and time-intelligence dimensions.
- **Power Automate Cloud Flow:**
  - Monthly recurrence trigger (1st of month @ 06:00 UTC).
  - Health check $\rightarrow$ Report generation $\rightarrow$ SharePoint archival $\rightarrow$ Office 365 Outlook board email.
  - Generates executive 2-page vector PDF report in 0.5 seconds.

---

## Slide 8: Technical Demonstration (Web Interface & APIs)
- **FastAPI Backend:** Interactive Swagger documentation at `/docs` with sub-15ms response times.
- **Demonstration UI:** Bloomberg-inspired financial intelligence dashboard:
  - Interactive multi-line revenue and expense charts.
  - Monthly P&L and Balance Sheet drill-downs.
  - Live Borrower Scorecard Calculator: underwriters adjust loan inputs and receive immediate FICO scores, risk tiers, and auto-approval recommendations.

---

## Slide 9: Engineering Challenges Faced & Solutions
1. **Challenge 1: Balance Sheet Imbalance:** In synthetic transaction generation, accounts receivable and payable fluctuations frequently cause balance sheet drift.
   - *Solution:* Implemented cash as the fundamental balancing asset account, mathematically enforcing `Assets = Liabilities + Equity` on every transaction batch.
2. **Challenge 2: Credit Class Imbalance:** In 16.4% default portfolios, models optimize for accuracy by ignoring defaults.
   - *Solution:* Applied Stratified 5-Fold Cross Validation and optimized decision thresholds via Youden's J-statistic on the ROC curve.
3. **Challenge 3: Portability for Evaluators:** External PostgreSQL or cloud Qlik licenses may not be installed on evaluation machines.
   - *Solution:* Engineered a dual-engine architecture: local zero-setup SQLite + bundled web app for instant demonstration, paired with production PostgreSQL DDL and Qlik `.qvs` load scripts.

---

## Slide 10: Conclusion, Results & Future Roadmap
- **Results:** 100% of functional requirements and evaluation criteria satisfied across all 5 modules; 17 out of 17 Pytest automated test cases passing.
- **Future Enhancements:**
  1. XGBoost and LightGBM gradient boosting benchmark comparisons with SHAP explainability.
  2. Multi-currency and multi-subsidiary consolidation engine for global enterprise ERPs.
  3. Real-time webhook ingestion for live core-banking ledger systems.
- **Thank you!** The FinSight platform is ready for technical review and public GitHub repository deployment.
