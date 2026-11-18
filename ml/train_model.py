"""
FinSight Platform - Credit Risk Machine Learning Training Engine
Implements:
1. Data Preprocessing & Target Leakage Prevention
2. Weight of Evidence (WOE) & Information Value (IV) Analysis
3. Stratified Train-Test Splitting & Class Imbalance Analysis
4. Logistic Regression Training with Hyperparameter Tuning
5. True Model Evaluation (ROC-AUC, Precision, Recall, F1, Confusion Matrix)
6. Basel II / FICO Credit Scorecard Integration
7. DB Synchronization (credit_predictions) & Artifact Serialization
"""

import os
import sys
import json
import sqlite3
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import matplotlib
matplotlib.use('Agg') # Headless rendering
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, confusion_matrix, classification_report
)

from ml.woe import WOETransformer
from ml.scorecard import CreditScorecard

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "finsight.db")
MODEL_ARTIFACT_PATH = os.path.join(BASE_DIR, "ml", "credit_risk_model.joblib")
METRICS_JSON_PATH = os.path.join(BASE_DIR, "ml", "metrics.json")
PLOTS_DIR = os.path.join(BASE_DIR, "docs", "screenshots")
os.makedirs(PLOTS_DIR, exist_ok=True)


def load_dataset():
    """Loads borrower and loan datasets from database."""
    print("[*] Fetching borrower credit dataset from database...")
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            b.borrower_id,
            b.annual_income,
            b.employment_length_years,
            b.home_ownership,
            b.state_code,
            l.loan_id,
            l.loan_amount,
            l.loan_term_months,
            l.interest_rate,
            l.installment_amount,
            l.loan_grade,
            l.debt_to_income_ratio,
            l.revolving_utilization_pct,
            l.total_credit_accounts,
            l.open_credit_accounts,
            l.derogatory_records,
            l.loan_purpose,
            l.is_default
        FROM loans l
        JOIN borrowers b ON l.borrower_id = b.borrower_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    print(f"[+] Loaded {len(df)} records. Target (is_default) class balance: {df['is_default'].value_counts().to_dict()}")
    return df


def train_credit_risk_pipeline():
    df = load_dataset()

    # Define Feature Sets
    features = [
        "annual_income",
        "employment_length_years",
        "home_ownership",
        "loan_amount",
        "loan_term_months",
        "interest_rate",
        "loan_grade",
        "debt_to_income_ratio",
        "revolving_utilization_pct",
        "total_credit_accounts",
        "open_credit_accounts",
        "derogatory_records",
        "loan_purpose"
    ]
    target = "is_default"

    X = df[features].copy()
    y = df[target].copy()

    # 1. Stratified Train-Test Split (80/20)
    print("[*] Splitting dataset into 80% train and 20% test using Stratified Sampling...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"    Train size: {len(X_train)} (Defaults: {y_train.sum()} = {(y_train.mean()*100):.2f}%)")
    print(f"    Test size:  {len(X_test)} (Defaults: {y_test.sum()} = {(y_test.mean()*100):.2f}%)")

    # 2. Weight of Evidence Transformation
    print("[*] Fitting Weight of Evidence (WOE) transformer on training set...")
    woe = WOETransformer(n_bins=5, smooth=0.5)
    woe.fit(X_train, y_train)

    X_train_woe = woe.transform(X_train)
    X_test_woe = woe.transform(X_test)

    iv_df = woe.get_woe_summary()
    print("\n--- INFORMATION VALUE (IV) SUMMARY ---")
    print(iv_df.to_string(index=False))

    # 3. Logistic Regression with Hyperparameter Tuning
    print("\n[*] Training Logistic Regression model with 5-fold Stratified Cross-Validation...")
    param_grid = {
        "C": [0.01, 0.1, 1.0, 5.0, 10.0],
        "penalty": ["l2"],
        "solver": ["lbfgs"],
        "class_weight": [None, "balanced"]
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(
        LogisticRegression(max_iter=1000, random_state=42),
        param_grid=param_grid,
        scoring="roc_auc",
        cv=cv,
        n_jobs=-1
    )
    grid.fit(X_train_woe, y_train)

    best_model = grid.best_estimator_
    print(f"[+] Best Hyperparameters: {grid.best_params_} (CV ROC-AUC: {grid.best_score_:.4f})")

    # 4. Evaluation on Unseen Test Dataset
    print("\n[*] Evaluating model on unseen holdout test set...")
    y_pred_proba = best_model.predict_proba(X_test_woe)[:, 1]
    
    # Select threshold using Youden's J statistic or optimal F1
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
    optimal_idx = np.argmax(tpr - fpr)
    optimal_threshold = float(thresholds[optimal_idx])
    
    # We will report standard 0.50 threshold and optimal risk threshold
    y_pred_default_th = (y_pred_proba >= 0.50).astype(int)
    y_pred_optimal_th = (y_pred_proba >= optimal_threshold).astype(int)

    test_roc_auc = float(roc_auc_score(y_test, y_pred_proba))
    test_accuracy = float(accuracy_score(y_test, y_pred_default_th))
    test_precision = float(precision_score(y_test, y_pred_default_th, zero_division=0))
    test_recall = float(recall_score(y_test, y_pred_default_th, zero_division=0))
    test_f1 = float(f1_score(y_test, y_pred_default_th, zero_division=0))

    cm = confusion_matrix(y_test, y_pred_default_th).tolist()

    print(f"    - ROC-AUC:    {test_roc_auc:.4f}")
    print(f"    - Accuracy:   {test_accuracy:.4f}")
    print(f"    - Precision:  {test_precision:.4f}")
    print(f"    - Recall:     {test_recall:.4f}")
    print(f"    - F1-Score:   {test_f1:.4f}")
    print(f"    - Confusion Matrix (TN, FP / FN, TP):\n      {cm}")

    # Precision-Recall curve
    precisions, recalls, pr_thresholds = precision_recall_curve(y_test, y_pred_proba)

    # 5. Scorecard Calibration
    scorecard = CreditScorecard(target_score=650, target_odds=20.0, pdo=20)

    # 6. Generate Publication Plots
    print("\n[*] Generating high-resolution model evaluation figures...")
    
    # Plot 1: ROC Curve
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color="#0284c7", lw=2.5, label=f"FinSight Model (AUC = {test_roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="#94a3b8", lw=1.5, linestyle="--", label="Random Classifier (AUC = 0.5000)")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold")
    plt.ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=11, fontweight="bold")
    plt.title("Credit Default Prediction - ROC Curve", fontsize=13, fontweight="bold")
    plt.legend(loc="lower right", frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "roc_curve.png"), dpi=200)
    plt.close()

    # Plot 2: Confusion Matrix Heatmap
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=["Good (Non-Default)", "Bad (Default)"],
        yticklabels=["Good (Non-Default)", "Bad (Default)"]
    )
    plt.xlabel("Predicted Outcome", fontsize=11, fontweight="bold")
    plt.ylabel("Actual Historical Outcome", fontsize=11, fontweight="bold")
    plt.title("Confusion Matrix (Holdout Test Set)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "confusion_matrix.png"), dpi=200)
    plt.close()

    # Plot 3: Information Value (IV) Feature Importance
    plt.figure(figsize=(9, 5))
    colors = ["#0284c7" if v >= 0.10 else "#94a3b8" for v in iv_df["Information_Value"]]
    plt.barh(iv_df["Feature"][::-1], iv_df["Information_Value"][::-1], color=colors[::-1])
    plt.axvline(0.02, color="#f59e0b", linestyle="--", label="Weak threshold (0.02)")
    plt.axvline(0.10, color="#10b981", linestyle="--", label="Medium threshold (0.10)")
    plt.axvline(0.30, color="#6366f1", linestyle="--", label="Strong threshold (0.30)")
    plt.xlabel("Information Value (IV)", fontsize=11, fontweight="bold")
    plt.title("Predictive Power Assessment via Information Value (IV)", fontsize=13, fontweight="bold")
    plt.legend(loc="lower right")
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "iv_feature_importance.png"), dpi=200)
    plt.close()

    # 7. Apply Predictions across Entire Database Portfolio
    print("\n[*] Scoring entire portfolio of 5,000 borrowers with trained scorecard...")
    X_all_woe = woe.transform(df[features])
    all_prob_defaults = best_model.predict_proba(X_all_woe)[:, 1]
    all_scores = scorecard.calculate_score(all_prob_defaults)
    all_risk_bands = [scorecard.get_risk_band(s) for s in all_scores]

    # Save to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM credit_predictions")

    predictions_records = []
    for idx, row in df.iterrows():
        predictions_records.append((
            int(row["loan_id"]),
            int(row["borrower_id"]),
            float(round(all_prob_defaults[idx], 4)),
            int(all_scores[idx]),
            str(all_risk_bands[idx]),
            float(round(X_all_woe.iloc[idx].sum(), 4)),
            "v1.0.0-logistic-woe"
        ))

    cursor.executemany("""
        INSERT INTO credit_predictions (
            loan_id, borrower_id, predicted_prob_default, credit_score, risk_band, woe_score, model_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, predictions_records)
    conn.commit()
    conn.close()
    print(f"[+] Loaded {len(predictions_records)} borrower credit scores into database.")

    # Plot 4: Credit Score Distribution
    plt.figure(figsize=(8, 5))
    sns.histplot(all_scores, bins=30, kde=True, color="#0284c7")
    plt.axvline(580, color="#ef4444", linestyle="--", label="Very High / High Threshold (580)")
    plt.axvline(650, color="#f59e0b", linestyle="--", label="Medium Risk Threshold (650)")
    plt.axvline(720, color="#10b981", linestyle="--", label="Low Risk Prime Threshold (720)")
    plt.xlabel("FICO-Scaled FinSight Credit Score (300 - 850)", fontsize=11, fontweight="bold")
    plt.ylabel("Borrower Count", fontsize=11, fontweight="bold")
    plt.title("Credit Risk Scorecard Portfolio Distribution", fontsize=13, fontweight="bold")
    plt.legend(loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "score_distribution.png"), dpi=200)
    plt.close()

    # 8. Save Artifacts & Metrics
    model_payload = {
        "model": best_model,
        "woe_transformer": woe,
        "scorecard": scorecard,
        "features": features,
        "optimal_threshold": optimal_threshold
    }
    joblib.dump(model_payload, MODEL_ARTIFACT_PATH)
    print(f"[+] Serialized model package saved to: {MODEL_ARTIFACT_PATH}")

    metrics_payload = {
        "model_type": "Logistic Regression with Weight of Evidence",
        "sample_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "overall_default_rate_pct": round(float(df["is_default"].mean() * 100.0), 2),
        "evaluation_metrics": {
            "roc_auc": round(test_roc_auc, 4),
            "accuracy": round(test_accuracy, 4),
            "precision": round(test_precision, 4),
            "recall": round(test_recall, 4),
            "f1_score": round(test_f1, 4),
            "optimal_decision_threshold": round(optimal_threshold, 4),
            "confusion_matrix": {
                "true_negatives": cm[0][0],
                "false_positives": cm[0][1],
                "false_negatives": cm[1][0],
                "true_positives": cm[1][1]
            }
        },
        "information_value_summary": iv_df.to_dict(orient="records"),
        "best_hyperparameters": grid.best_params_
    }

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=4)
    print(f"[+] Real evaluation metrics stored in: {METRICS_JSON_PATH}")

    print("\n[SUCCESS] Credit Risk Modeling Module completed successfully!")
    return metrics_payload

if __name__ == "__main__":
    train_credit_risk_pipeline()
