# FinSight – Individual Project Reflection & Learning Document

**Author:** Technical Engineering Intern  
**Internship Organization:** Nexvia Technologies  
**Project:** Financial Analytics and Risk Reporting System (FinSight)  
**Date:** November 2026

---

## 1. Executive Summary & Project Context

The objective of this assignment was to conceptualize, design, and construct an enterprise-grade Financial Analytics and Credit Risk Reporting platform (**FinSight**). Unlike academic projects that focus strictly on training a machine learning model or building a static frontend mock-up, this project demanded end-to-end integration across six disparate disciplines:
1. Double-entry accounting principles and financial statement modeling.
2. Advanced relational database design (PostgreSQL/SQLite DDL, CTEs, Window functions).
3. Statistical credit risk modeling (Weight of Evidence, Information Value, Basel II scorecard scaling).
4. Business intelligence architecture (Qlik Sense load scripts, Star/Snowflake schemas, Set Analysis).
5. Robotic process automation and cloud workflow orchestration (Microsoft Power Automate).
6. Full-stack microservice engineering (FastAPI REST APIs, responsive enterprise UI, headless vector PDF generation).

---

## 2. Technical Journey & Architectural Decisions

### A. Accounting Integrity & Double-Entry Modeling
One of the most valuable lessons was translating GAAP accounting identities into relational database constraints. Early in development, generating independent synthetic numbers for revenue, expenses, and balance sheet accounts led to the classic "unbalanced balance sheet" problem where Assets $\neq$ Liabilities + Equity.

To solve this, I designed a strict double-entry ledger pipeline:
- Every revenue recognition credited an income account and debited Accounts Receivable or Cash.
- Net profit from the income statement was dynamically capitalized into Retained Earnings month-over-month.
- Cash was computed as the balancing asset account:
$$\text{Cash} = (\text{Liabilities} + \text{Equity}) - (\text{AR} + \text{Inventory} + \text{Net Fixed Assets} + \text{Other Assets})$$
This mathematically guaranteed that across all 12 fiscal months, the discrepancy between Total Assets and Total Liabilities + Equity was exactly **$0.00**.

### B. Credit Risk Engineering: Moving Beyond Raw Accuracy
In introductory machine learning, students often optimize for accuracy. However, in credit risk with a 16.4% default rate, a model predicting 100% "Good" achieves 83.6% accuracy while resulting in total financial insolvency for the lending institution.

Implementing **Weight of Evidence (WOE)** and **Information Value (IV)** proved transformative:
- WOE transformed non-linear variables into linear log-odds space, making standard Logistic Regression highly robust and interpretable.
- Binned variables allowed straightforward handling of extreme outliers without discarding borrower data.
- The resulting Logistic Regression model achieved a genuine **ROC-AUC of 0.8469**, a Precision of **63.8%**, and a Recall of **40.9%** on the unseen test set.
- Calibrating the **Basel II Scorecard formula** ($\text{Score} = \text{Offset} + \text{Factor} \times \ln(\text{Odds})$) with $\text{PDO} = 20$ provided an intuitive FICO-like scale (300 to 850) that non-technical underwriters can easily understand.

### C. Portable Microservice & Enterprise UX
Recognizing that evaluation environments vary, I implemented a zero-setup architecture:
- SQLite (`finsight.db`) is bundled and populated out of the box so that any evaluator can immediately run `pytest` or `uvicorn backend.main:app` without configuring external databases.
- At the same time, full production **PostgreSQL DDL (`database/schema.sql`)** and **Qlik load scripts (`qlik/load_scripts/`)** are included for enterprise-scale deployments.
- The web interface was inspired by the clean, dense visual hierarchy of modern financial terminals like Bloomberg and Stripe, offering instant responsiveness, live scorecard simulation, and one-click PDF board report downloads.

---

## 3. Key Concepts Learned & Competencies Demonstrated

| Domain | Key Concepts Learned & Implemented |
| :--- | :--- |
| **Financial Engineering** | GAAP P&L statement flow, EBITDA vs EBIT, Balance Sheet equation, Retained Earnings capitalization, MoM growth calculations, Budget variance analysis. |
| **Database & SQL** | CTEs, Window functions (`LAG() OVER()`), relational foreign key cascading, index optimization, SQL reporting views. |
| **Machine Learning** | Weight of Evidence (WOE), Information Value (IV), Laplace smoothing, stratified sampling, ROC-AUC optimization, confusion matrix trade-offs, Basel II scorecard scaling. |
| **Business Intelligence** | Qlik Sense scripting syntax, synthetic key elimination, master dimension/measure creation, Set Analysis logic. |
| **Automation** | Microsoft Power Automate Cloud Flows, scheduled recurrence triggers, Office 365 Outlook HTML templates, ReportLab vector PDF styling. |
| **Software Architecture** | FastAPI asynchronous endpoints, Pydantic data validation, Pytest testing suite, CORS configuration, responsive Tailwind CSS styling. |

---

## 4. Conclusion

This project has solidified my capabilities as a well-rounded Data Engineer, Financial Analyst, and Software Architect. I am proud to submit the **FinSight Platform** to the Nexvia Technologies technical evaluation team.
