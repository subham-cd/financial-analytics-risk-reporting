"""
FinSight Platform - Credit Risk Intelligence & Scorecard API Routes
"""

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from backend.app.database import execute_query, execute_one
from ml.predict import predict_single_borrower

router = APIRouter(prefix="/api/credit-risk", tags=["Credit Risk"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METRICS_JSON_PATH = os.path.join(BASE_DIR, "ml", "metrics.json")


class BorrowerInput(BaseModel):
    annual_income: float = Field(..., ge=10000, le=1000000, description="Annual income in USD")
    employment_length_years: float = Field(..., ge=0, le=45, description="Years in current employment")
    home_ownership: Literal["RENT", "OWN", "MORTGAGE", "OTHER"] = Field("RENT", description="Home ownership type")
    loan_amount: float = Field(..., ge=1000, le=100000, description="Requested principal amount in USD")
    loan_term_months: Literal[36, 60] = Field(36, description="Loan term in months (36 or 60)")
    interest_rate: float = Field(..., ge=3.0, le=36.0, description="Assigned APR interest rate")
    loan_grade: Literal["A", "B", "C", "D", "E", "F"] = Field("B", description="Lending grade")
    debt_to_income_ratio: float = Field(..., ge=0, le=100, description="Debt to income ratio percentage")
    revolving_utilization_pct: float = Field(..., ge=0, le=100, description="Revolving credit line utilization percentage")
    total_credit_accounts: int = Field(..., ge=1, le=100, description="Total credit lines in bureau file")
    open_credit_accounts: int = Field(..., ge=1, le=50, description="Open credit lines")
    derogatory_records: int = Field(0, ge=0, le=20, description="Number of public derogatory records")
    loan_purpose: str = Field("debt_consolidation", description="Purpose of loan")


@router.get("/summary")
def get_credit_risk_summary():
    """Returns portfolio-level credit risk intelligence, grade-level default rates, and ML metrics."""
    
    # Portfolio Aggregations
    portfolio = execute_one("""
        SELECT 
            COUNT(loan_id) AS total_loans,
            ROUND(SUM(loan_amount), 2) AS total_funded_volume,
            ROUND(AVG(loan_amount), 2) AS avg_loan_amount,
            ROUND(AVG(interest_rate), 2) AS avg_interest_rate,
            ROUND(AVG(debt_to_income_ratio), 2) AS avg_dti,
            SUM(is_default) AS total_defaults,
            ROUND((SUM(is_default) * 1.0 / COUNT(loan_id)) * 100.0, 2) AS default_rate_pct
        FROM loans
    """)

    # Default Rate by Loan Grade
    grade_distribution = execute_query("""
        SELECT 
            l.loan_grade,
            COUNT(l.loan_id) AS loan_count,
            ROUND(SUM(l.loan_amount), 2) AS total_funded_amount,
            ROUND(AVG(l.interest_rate), 2) AS avg_interest_rate,
            ROUND(AVG(l.debt_to_income_ratio), 2) AS avg_dti,
            SUM(l.is_default) AS default_count,
            ROUND((SUM(l.is_default) * 1.0 / COUNT(l.loan_id)) * 100.0, 2) AS default_rate_pct,
            ROUND(AVG(p.predicted_prob_default) * 100.0, 2) AS avg_predicted_default_pct,
            ROUND(AVG(p.credit_score), 0) AS avg_credit_score
        FROM loans l
        LEFT JOIN credit_predictions p ON l.loan_id = p.loan_id
        GROUP BY l.loan_grade
        ORDER BY l.loan_grade
    """)

    # Scorecard Risk Band Distribution
    risk_bands = execute_query("""
        SELECT 
            p.risk_band,
            COUNT(p.prediction_id) AS borrower_count,
            ROUND(COUNT(p.prediction_id) * 100.0 / (SELECT COUNT(*) FROM credit_predictions), 2) AS portfolio_share_pct,
            ROUND(AVG(p.predicted_prob_default) * 100.0, 2) AS avg_default_prob_pct,
            ROUND(AVG(p.credit_score), 0) AS avg_credit_score,
            ROUND(SUM(l.loan_amount), 2) AS total_exposure_amount
        FROM credit_predictions p
        JOIN loans l ON p.loan_id = l.loan_id
        GROUP BY p.risk_band
        ORDER BY AVG(p.credit_score) DESC
    """)

    # Read ML evaluation metrics from disk
    ml_metrics = {}
    if os.path.exists(METRICS_JSON_PATH):
        try:
            with open(METRICS_JSON_PATH, "r", encoding="utf-8") as f:
                ml_metrics = json.load(f)
        except Exception:
            pass

    return {
        "status": "success",
        "portfolio_overview": portfolio,
        "grade_distribution": grade_distribution,
        "risk_band_distribution": risk_bands,
        "ml_model_evaluation": ml_metrics
    }


@router.post("/predict")
def predict_borrower_credit_risk(payload: BorrowerInput):
    """
    Evaluates borrower creditworthiness in real time using the trained Weight of Evidence
    Logistic Regression model and FICO scorecard scaling.
    """
    try:
        result = predict_single_borrower(payload.model_dump())
        return {
            "status": "success",
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
