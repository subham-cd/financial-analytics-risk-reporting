"""
FinSight Platform - Jupyter Notebook Generator
Creates:
1. notebooks/exploratory_analysis.ipynb (Financial Statement & Budget Analysis)
2. notebooks/credit_risk_analysis.ipynb (Machine Learning Credit Risk & Scorecard Modeling)
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOKS_DIR = os.path.join(BASE_DIR, "notebooks")
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

def create_pnl_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# FinSight – Financial Statement & Budget Variance Analysis\n",
                    "**Project:** Financial Analytics and Risk Reporting System (Nexvia Internship Evaluation)\n",
                    "**Objective:** Ingest double-entry transaction ledgers, calculate GAAP P&L metrics, verify Balance Sheet reconciliation, and identify budget variances."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import sqlite3\n",
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "\n",
                    "# Connect to FinSight SQLite Database\n",
                    "conn = sqlite3.connect('../finsight.db')\n",
                    "print('Database connected successfully.')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Monthly Profit & Loss Statement\n",
                    "Extract calculated revenue, COGS, EBITDA, and net profit from SQL reporting views."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "query_pnl = 'SELECT * FROM view_monthly_pnl ORDER BY fiscal_month'\n",
                    "df_pnl = pd.read_sql(query_pnl, conn)\n",
                    "df_pnl['gross_margin_%'] = (df_pnl['gross_profit'] / df_pnl['total_revenue'] * 100).round(2)\n",
                    "df_pnl['net_margin_%'] = (df_pnl['net_profit'] / df_pnl['total_revenue'] * 100).round(2)\n",
                    "display(df_pnl[['fiscal_month', 'total_revenue', 'cogs', 'gross_profit', 'ebitda', 'net_profit', 'gross_margin_%', 'net_margin_%']])"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Balance Sheet Reconciliation Verification\n",
                    "Verify that Assets = Liabilities + Equity for all 12 fiscal months."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "query_bs = '''\n",
                    "    SELECT \n",
                    "        a.fiscal_month,\n",
                    "        ROUND(SUM(a.net_value), 2) AS total_assets,\n",
                    "        ROUND((SELECT SUM(l.current_balance) FROM liabilities l WHERE l.fiscal_month = a.fiscal_month), 2) AS total_liabilities,\n",
                    "        ROUND((SELECT SUM(e.total_equity) FROM equity e WHERE e.fiscal_month = a.fiscal_month), 2) AS total_equity\n",
                    "    FROM assets a\n",
                    "    GROUP BY a.fiscal_month\n",
                    "'''\n",
                    "df_bs = pd.read_sql(query_bs, conn)\n",
                    "df_bs['discrepancy'] = (df_bs['total_assets'] - (df_bs['total_liabilities'] + df_bs['total_equity'])).round(2)\n",
                    "df_bs['is_reconciled'] = df_bs['discrepancy'].abs() < 0.01\n",
                    "display(df_bs)\n",
                    "print('All months reconciled:', df_bs['is_reconciled'].all())"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Department Budget vs Actual Variance\n",
                    "Analyze which departments are exceeding budgets and driving financial variances."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {},
                "outputs": [],
                "source": [
                    "query_bva = '''\n",
                    "    SELECT \n",
                    "        department_name,\n",
                    "        ROUND(SUM(budgeted_amount), 2) AS total_budget,\n",
                    "        ROUND(SUM(actual_amount), 2) AS total_actual,\n",
                    "        ROUND(SUM(actual_amount) - SUM(budgeted_amount), 2) AS variance_amount,\n",
                    "        ROUND(((SUM(actual_amount) - SUM(budgeted_amount)) / NULLIF(SUM(budgeted_amount), 0)) * 100.0, 2) AS variance_pct\n",
                    "    FROM view_budget_vs_actual\n",
                    "    WHERE account_type = 'Expense'\n",
                    "    GROUP BY department_name\n",
                    "    ORDER BY variance_amount DESC\n",
                    "'''\n",
                    "df_bva = pd.read_sql(query_bva, conn)\n",
                    "display(df_bva)"
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python", "version": "3.12.3"},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    with open(os.path.join(NOTEBOOKS_DIR, "exploratory_analysis.ipynb"), "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

def create_credit_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# FinSight – Machine Learning Credit Risk Scoring & Scorecard Modeling\n",
                    "**Project:** Financial Analytics and Risk Reporting System (Nexvia Internship Evaluation)\n",
                    "**Methodology:** Lending Club Portfolio Modeling, Weight of Evidence (WOE), Information Value (IV), Logistic Regression, and FICO Scorecard Calibration."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import os, sys\n",
                    "sys.path.append('..')\n",
                    "import sqlite3\n",
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "from ml.woe import WOETransformer\n",
                    "from ml.scorecard import CreditScorecard\n",
                    "from sklearn.linear_model import LogisticRegression\n",
                    "from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, classification_report\n",
                    "\n",
                    "conn = sqlite3.connect('../finsight.db')\n",
                    "df = pd.read_sql('SELECT * FROM loans l JOIN borrowers b ON l.borrower_id=b.borrower_id', conn)\n",
                    "print(f'Loaded {len(df)} loans. Overall Default Rate: {(df[\"is_default\"].mean()*100):.2f}%')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Information Value (IV) & Feature Selection\n",
                    "Evaluate predictive strength of borrower credit attributes via Weight of Evidence (WOE)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "features = ['loan_grade', 'interest_rate', 'debt_to_income_ratio', 'revolving_utilization_pct', 'derogatory_records', 'annual_income']\n",
                    "X = df[features]\n",
                    "y = df['is_default']\n",
                    "\n",
                    "woe = WOETransformer(n_bins=5)\n",
                    "woe.fit(X, y)\n",
                    "display(woe.get_woe_summary())"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Logistic Regression Model Training & True Evaluation\n",
                    "Train Logistic Regression classifier on WOE-transformed features."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": [
                    "X_woe = woe.transform(X)\n",
                    "clf = LogisticRegression(max_iter=1000, random_state=42)\n",
                    "clf.fit(X_woe, y)\n",
                    "y_probs = clf.predict_proba(X_woe)[:, 1]\n",
                    "auc = roc_auc_score(y, y_probs)\n",
                    "print(f'Model Full Portfolio ROC-AUC: {auc:.4f}')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Scorecard Scaling (Basel II / FICO Formula)\n",
                    "Scale probabilities into standardized 300-850 scores: Score = Offset + Factor * ln(Odds)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {},
                "outputs": [],
                "source": [
                    "card = CreditScorecard(target_score=650, target_odds=20.0, pdo=20)\n",
                    "scores = card.calculate_score(y_probs)\n",
                    "df['credit_score'] = scores\n",
                    "df['risk_band'] = [card.get_risk_band(s) for s in scores]\n",
                    "print('Score distribution by Risk Band:')\n",
                    "display(df.groupby('risk_band')['credit_score'].agg(['count', 'min', 'mean', 'max']))"
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python", "version": "3.12.3"},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    with open(os.path.join(NOTEBOOKS_DIR, "credit_risk_analysis.ipynb"), "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

if __name__ == "__main__":
    create_pnl_notebook()
    create_credit_notebook()
    print("[SUCCESS] Jupyter Notebooks generated in notebooks/")
