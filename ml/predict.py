"""
FinSight Platform - Real-Time Credit Risk Inference Engine
Exposes high-performance prediction interface for single borrowers or batch requests.
"""

import os
import sys
import joblib
import pandas as pd
from typing import Dict, Any, Union

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.woe import WOETransformer
from ml.scorecard import CreditScorecard

MODEL_ARTIFACT_PATH = os.path.join(BASE_DIR, "ml", "credit_risk_model.joblib")

_model_bundle = None

def get_model_bundle():
    global _model_bundle
    if _model_bundle is None:
        if not os.path.exists(MODEL_ARTIFACT_PATH):
            raise FileNotFoundError(f"Model artifact not found at {MODEL_ARTIFACT_PATH}. Run ml/train_model.py first.")
        _model_bundle = joblib.load(MODEL_ARTIFACT_PATH)
    return _model_bundle

def predict_single_borrower(borrower_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predicts default probability and FICO-scaled credit score for a single borrower.
    Expected keys:
        annual_income, employment_length_years, home_ownership, loan_amount,
        loan_term_months, interest_rate, loan_grade, debt_to_income_ratio,
        revolving_utilization_pct, total_credit_accounts, open_credit_accounts,
        derogatory_records, loan_purpose
    """
    bundle = get_model_bundle()
    model = bundle["model"]
    woe = bundle["woe_transformer"]
    scorecard = bundle["scorecard"]
    features = bundle["features"]

    # Construct single-row DataFrame
    df_input = pd.DataFrame([borrower_data])

    # Fallback default values for missing attributes
    defaults = {
        "annual_income": 65000.0,
        "employment_length_years": 3.0,
        "home_ownership": "RENT",
        "loan_amount": 10000.0,
        "loan_term_months": 36,
        "interest_rate": 12.0,
        "loan_grade": "B",
        "debt_to_income_ratio": 18.0,
        "revolving_utilization_pct": 45.0,
        "total_credit_accounts": 15,
        "open_credit_accounts": 8,
        "derogatory_records": 0,
        "loan_purpose": "debt_consolidation"
    }
    for col in features:
        if col not in df_input.columns:
            df_input[col] = defaults[col]

    df_features = df_input[features].copy()

    # WOE transformation
    df_woe = woe.transform(df_features)

    # Model inference
    prob_default = float(model.predict_proba(df_woe)[0, 1])
    evaluation = scorecard.evaluate_borrower(prob_default)

    # Detailed response
    return {
        "borrower_inputs": borrower_data,
        "predicted_prob_default": evaluation["predicted_prob_default"],
        "predicted_prob_default_pct": evaluation["predicted_prob_default_pct"],
        "credit_score": evaluation["credit_score"],
        "risk_band": evaluation["risk_band"],
        "underwriting_recommendation": evaluation["underwriting_recommendation"],
        "model_version": "v1.0.0-logistic-woe",
        "decision": "APPROVED" if evaluation["risk_band"] in ["Low Risk", "Medium Risk"] else "MANUAL_REVIEW" if evaluation["risk_band"] == "High Risk" else "DECLINED"
    }

if __name__ == "__main__":
    sample_borrower = {
        "annual_income": 85000.0,
        "employment_length_years": 5.0,
        "home_ownership": "MORTGAGE",
        "loan_amount": 15000.0,
        "loan_term_months": 36,
        "interest_rate": 8.5,
        "loan_grade": "A",
        "debt_to_income_ratio": 14.2,
        "revolving_utilization_pct": 28.0,
        "total_credit_accounts": 20,
        "open_credit_accounts": 10,
        "derogatory_records": 0,
        "loan_purpose": "debt_consolidation"
    }
    result = predict_single_borrower(sample_borrower)
    print("Sample Inference Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
