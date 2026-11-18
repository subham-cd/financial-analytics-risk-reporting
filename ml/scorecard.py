"""
FinSight Platform - Basel II / FICO Credit Risk Scorecard Engine
Scales logistic regression default probabilities and log-odds into standard 300-850 credit scores.

Mathematical Formulation:
    Odds = P(Good) / P(Bad) = (1 - P(Default)) / P(Default)
    Factor = PDO / ln(2)
    Offset = Target_Score - (Factor * ln(Target_Odds))
    Credit_Score = Offset + (Factor * ln(Odds))

Calibration Parameters:
    Target Score: 650 at 20:1 Odds
    Points to Double the Odds (PDO): 20
    Score Range: 300 to 850
"""

import numpy as np
from typing import Dict, Union, Tuple


class CreditScorecard:
    def __init__(
        self,
        target_score: float = 650.0,
        target_odds: float = 20.0,
        pdo: float = 20.0,
        min_score: int = 300,
        max_score: int = 850
    ):
        self.target_score = target_score
        self.target_odds = target_odds
        self.pdo = pdo
        self.min_score = min_score
        self.max_score = max_score

        # Calculate Factor and Offset
        self.factor = self.pdo / np.log(2.0)
        self.offset = self.target_score - (self.factor * np.log(self.target_odds))

    def calculate_score(self, prob_default: Union[float, np.ndarray]) -> Union[int, np.ndarray]:
        """
        Converts default probability into scaled credit score (300 - 850).
        """
        prob = np.clip(np.array(prob_default), 1e-6, 1.0 - 1e-6)
        # Good / Bad odds
        odds = (1.0 - prob) / prob
        raw_score = self.offset + (self.factor * np.log(odds))
        scaled_score = np.clip(np.round(raw_score), self.min_score, self.max_score).astype(int)
        
        if np.ndim(prob_default) == 0:
            return int(scaled_score)
        return scaled_score

    def get_risk_band(self, score: int) -> str:
        """Classifies borrower into standardized risk tiers."""
        if score >= 720:
            return "Low Risk"
        elif score >= 650:
            return "Medium Risk"
        elif score >= 580:
            return "High Risk"
        else:
            return "Very High Risk"

    def evaluate_borrower(self, prob_default: float) -> Dict[str, Union[float, int, str]]:
        """Complete borrower-level risk scoring evaluation."""
        score = self.calculate_score(prob_default)
        risk_band = self.get_risk_band(score)
        
        # Recommendation
        if risk_band == "Low Risk":
            recommendation = "Auto-Approve: Prime Tier terms with lowest APR"
        elif risk_band == "Medium Risk":
            recommendation = "Approve: Standard terms with standard underwriting review"
        elif risk_band == "High Risk":
            recommendation = "Conditional Review: Requires collateral or debt co-signer"
        else:
            recommendation = "Decline / High Risk: Probability of default exceeds risk tolerance threshold"

        return {
            "predicted_prob_default": round(float(prob_default), 4),
            "predicted_prob_default_pct": round(float(prob_default) * 100.0, 2),
            "credit_score": int(score),
            "risk_band": risk_band,
            "underwriting_recommendation": recommendation
        }
