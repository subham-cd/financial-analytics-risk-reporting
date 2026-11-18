"""
FinSight Platform - Weight of Evidence (WOE) and Information Value (IV) Engine
Mathematically rigorous feature transformation and predictive power assessment for credit risk modeling.

Formulas:
    WOE_i = ln( (Good_i / Total_Good) / (Bad_i / Total_Bad) )
    IV_i  = ( (Good_i / Total_Good) - (Bad_i / Total_Bad) ) * WOE_i
    Total_IV = SUM(IV_i)

Interpretation of Information Value (IV):
    < 0.02      : Not predictive / Useless
    0.02 to 0.10: Weak predictive power
    0.10 to 0.30: Medium predictive power
    0.30 to 0.50: Strong predictive power
    > 0.50      : Suspicious / Check for target leakage
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Union


class WOETransformer:
    def __init__(self, n_bins: int = 5, smooth: float = 0.5):
        """
        Args:
            n_bins: Number of quantile bins for continuous variables.
            smooth: Smoothing factor (Laplace-style) to prevent division by zero or ln(0).
        """
        self.n_bins = n_bins
        self.smooth = smooth
        self.woe_dict: Dict[str, Dict] = {}
        self.iv_summary: pd.DataFrame = None
        self.bin_edges: Dict[str, List[float]] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'WOETransformer':
        """
        Calculates WOE and IV for each feature in X against binary target y.
        y: 1 for Bad (Default), 0 for Good (Non-default).
        """
        total_bad = (y == 1).sum()
        total_good = (y == 0).sum()

        if total_bad == 0 or total_good == 0:
            raise ValueError("Target variable must contain both Good (0) and Bad (1) outcomes.")

        iv_records = []

        for col in X.columns:
            series = X[col].copy()
            is_numeric = pd.api.types.is_numeric_dtype(series)

            # Binning continuous variables
            if is_numeric and series.nunique() > self.n_bins:
                try:
                    # Quantile binning with unique bin edges
                    bins = pd.qcut(series, q=self.n_bins, duplicates='drop')
                    bin_edges = list(pd.qcut(series, q=self.n_bins, duplicates='drop', retbins=True)[1])
                    self.bin_edges[col] = bin_edges
                except Exception:
                    # Fallback to cut
                    bins = pd.cut(series, bins=self.n_bins)
                    self.bin_edges[col] = list(pd.cut(series, bins=self.n_bins, retbins=True)[1])
                binned_col = bins.astype(str)
            else:
                binned_col = series.astype(str)

            # Calculate frequency of Good and Bad in each bin
            contingency = pd.crosstab(binned_col, y)
            
            # Ensure columns 0 and 1 exist
            good_counts = contingency[0] if 0 in contingency.columns else pd.Series(0, index=contingency.index)
            bad_counts = contingency[1] if 1 in contingency.columns else pd.Series(0, index=contingency.index)

            # Apply smoothing to avoid zero divisions
            dist_good = (good_counts + self.smooth) / (total_good + 2 * self.smooth)
            dist_bad = (bad_counts + self.smooth) / (total_bad + 2 * self.smooth)

            woe = np.log(dist_good / dist_bad)
            iv = (dist_good - dist_bad) * woe
            total_iv = iv.sum()

            # Store mapping
            self.woe_dict[col] = woe.to_dict()

            # Predictive power category
            if total_iv < 0.02:
                strength = "Unpredictive (<0.02)"
            elif total_iv < 0.10:
                strength = "Weak (0.02-0.10)"
            elif total_iv < 0.30:
                strength = "Medium (0.10-0.30)"
            elif total_iv <= 0.50:
                strength = "Strong (0.30-0.50)"
            else:
                strength = "Very Strong / Suspicious (>0.50)"

            iv_records.append({
                "Feature": col,
                "Information_Value": round(total_iv, 4),
                "Predictive_Strength": strength,
                "Bins_Count": len(woe)
            })

        self.iv_summary = pd.DataFrame(iv_records).sort_values(by="Information_Value", ascending=False).reset_index(drop=True)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw input features into their respective WOE values."""
        X_woe = pd.DataFrame(index=X.index)

        for col in X.columns:
            if col not in self.woe_dict:
                continue

            series = X[col].copy()
            mapping = self.woe_dict[col]

            if col in self.bin_edges:
                edges = self.bin_edges[col]
                # Bin new continuous data according to training bin edges
                bins = pd.cut(series, bins=edges, include_lowest=True).astype(str)
                X_woe[f"{col}_woe"] = bins.map(mapping).fillna(0.0)
            else:
                X_woe[f"{col}_woe"] = series.astype(str).map(mapping).fillna(0.0)

        return X_woe

    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        self.fit(X, y)
        return self.transform(X)

    def get_woe_summary(self) -> pd.DataFrame:
        """Returns the Information Value summary across all processed features."""
        return self.iv_summary
