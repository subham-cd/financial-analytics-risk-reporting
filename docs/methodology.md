# FinSight – Credit Risk Modeling Methodology

## 1. Credit Risk Modeling Overview

Credit scoring models estimate the **Probability of Default ($PD$)** of loan applicants over a defined horizon (typically 12 or 24 months). Under the **Basel II/III internal ratings-based (IRB) framework**, credit institutions must calculate three core credit risk parameters:

1. **Probability of Default (PD)**: Likelihood that a borrower fails to meet debt obligations.
2. **Exposure at Default (EAD)**: Total gross dollar exposure outstanding at the moment of default.
3. **Loss Given Default (LGD)**: Proportion of the loan exposure lost after collateral recovery and legal collection efforts.

The FinSight platform implements the **PD Estimation Engine** utilizing **Weight of Evidence (WOE)** transformation, **Information Value (IV)** screening, and **L2-penalized Logistic Regression**.

---

## 2. Weight of Evidence (WOE) & Information Value (IV)

### Mathematical Formulation
For each explanatory variable $X$ partitioned into $k$ discrete bins:

$$\text{WOE}_i = \ln\left(\frac{\text{Good}_i / \text{Total Good}}{\text{Bad}_i / \text{Total Bad}}\right)$$

Where:
- $\text{Good}_i$: Count of non-defaulting loans in bin $i$ ($\text{is\_default} = 0$).
- $\text{Bad}_i$: Count of defaulted loans in bin $i$ ($\text{is\_default} = 1$).
- $\text{Total Good}, \text{Total Bad}$: Overall population counts.

Information Value (IV) aggregates the predictive power across all $k$ bins:

$$\text{IV} = \sum_{i=1}^{k} \left(\frac{\text{Good}_i}{\text{Total Good}} - \frac{\text{Bad}_i}{\text{Total Bad}}\right) \times \text{WOE}_i$$

### Industry Benchmark Interpretation of IV
- **$\text{IV} < 0.02$**: Not predictive; candidate for elimination.
- **$0.02 \le \text{IV} < 0.10$**: Weak predictive power.
- **$0.10 \le \text{IV} < 0.30$**: Medium predictive power.
- **$0.30 \le \text{IV} \le 0.50$**: Strong predictive power.
- **$\text{IV} > 0.50$**: Extremely strong; investigated for potential **target leakage**.

### Empirical FinSight IV Results
In the FinSight 5,000 borrower portfolio, our training run calculated:
- `loan_grade`: $\text{IV} = 1.6610$ (Strong monotonic driver)
- `interest_rate`: $\text{IV} = 1.4479$ (Strong risk signal)
- `revolving_utilization_pct`: $\text{IV} = 1.2745$ (Strong liquidity stress indicator)
- `debt_to_income_ratio`: $\text{IV} = 1.0848$ (Strong leverage measure)
- `derogatory_records`: $\text{IV} = 0.3490$ (Strong bureau history signal)

---

## 3. Why Accuracy Alone Is Deceptive in Credit Risk

In retail lending portfolios, defaults are relatively rare events (typically 5% to 18% of total loans). In our portfolio, defaults comprise **16.4%** of loans.

### The Accuracy Paradox:
Consider a naive "dumb" model that always predicts every applicant will **NOT** default:
$$\text{Accuracy} = \frac{\text{True Negatives}}{\text{Total Applicants}} = \frac{4,181}{5,000} = 83.6\%$$

Despite boasting **83.6% accuracy**, this naive model has:
- **Recall on Defaults**: $0.0\%$ (Zero defaulted loans detected!)
- **Precision on Defaults**: Undefined ($0/0$)
- **Financial Result**: Catastrophic credit losses, loan defaults are completely unmitigated.

### Critical Evaluation Metrics in FinSight:
1. **ROC-AUC (Receiver Operating Characteristic - Area Under Curve)**:
   Measures ranking ability: the probability that a randomly chosen defaulting borrower receives a higher risk score than a non-defaulting borrower. FinSight achieved an **ROC-AUC of 0.8469**.
2. **Precision & Recall on Bad Accounts**:
   FinSight achieved Precision of **63.8%** and Recall of **40.9%** at the default threshold, successfully flagging high-risk borrowers while keeping false declines minimal.
3. **Confusion Matrix Analysis**:
   On the 1,000-borrower holdout test set:
   - True Negatives (Good predicted Good): **798**
   - False Positives (Good predicted Bad): **38** (Low friction for creditworthy applicants)
   - False Negatives (Bad predicted Good): **97**
   - True Positives (Bad predicted Bad): **67**

---

## 4. Scorecard Scaling (Basel II / FICO Standards)

To present risk in an interpretable format for underwriters, loan officers, and borrowers, the model's predicted probabilities are converted into a standard **300 to 850 credit score**.

### Formula:
$$\text{Score} = \text{Offset} + \text{Factor} \times \ln(\text{Odds})$$

Where:
$$\text{Odds} = \frac{P(\text{Good})}{P(\text{Bad})} = \frac{1 - P(\text{Default})}{P(\text{Default})}$$
$$\text{Factor} = \frac{\text{PDO}}{\ln(2)}$$
$$\text{Offset} = \text{Target Score} - \text{Factor} \times \ln(\text{Target Odds})$$

### Calibration:
- **Target Score**: 650
- **Target Odds**: 20:1
- **Points to Double the Odds (PDO)**: 20 points
- **Resulting Parameters**: $\text{Factor} \approx 28.854$, $\text{Offset} \approx 563.56$

### Underwriting Risk Tiers:
- **Low Risk ($\text{Score} \ge 720$)**: Prime applicants. Low default probability ($< 5\%$). Recommended for **Auto-Approval** with lowest APR.
- **Medium Risk ($650 \le \text{Score} < 720$)**: Standard applicants. Recommended for **Approval** with standard underwriting.
- **High Risk ($580 \le \text{Score} < 650$)**: Subprime exposure. Recommended for **Manual Underwriter Review** or debt co-signer requirement.
- **Very High Risk ($\text{Score} < 580$)**: Deep subprime. High default probability ($> 30\%$). Recommended for **Decline**.
