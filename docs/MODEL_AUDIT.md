# Model Audit — GovProject Cost & Time Overrun Prediction

## 1. Model Overview

| Property | Value |
|---|---|
| **Model Type** | MultiOutputRegressor wrapping XGBRegressor |
| **Pipeline** | sklearn Pipeline: ColumnTransformer → MultiOutputRegressor |
| **Artifact** | `model/models/sih_cost_prediction_model.pkl` (joblib dict) |
| **Targets** | `Overrun_Amount` (₹ Crore), `Time_Overrun_Months` (months) |
| **Features** | Sector (categorical, one-hot), Original_Cost, Physical_Progress, Time_Delay_Months |
| **Training Data** | ~24,000 rows from government flash reports (PDF-extracted) |
| **Framework** | scikit-learn + XGBoost |

## 2. Model Inputs

| Feature | Type | Unit | Range | Description |
|---|---|---|---|---|
| Sector | Categorical | — | 7 canonical sectors | Project infrastructure sector |
| Original_Cost | Float | ₹ Crore | > 0 | Originally approved project cost |
| Physical_Progress | Float | % | 0–100 | Current completion percentage |
| Time_Delay_Months | Float | months | ≥ 0 | Existing time delay in months |

### Sector Aliases
The model normalizes sector names to canonical forms:
- `road transport highways` ← road, highway, NH, expressway
- `railways` ← rail, metro rail
- `power` ← solar, thermal, wind, hydro
- `petroleum` ← oil, gas, LPG
- `water resources` ← irrigation, dam, canal
- `urban development` ← housing, airport, smart city
- `telecommunication` ← telecom, mobile

## 3. Model Outputs

| Output | Unit | Description |
|---|---|---|
| `cost_overrun_crore` | ₹ Crore | Predicted additional cost beyond original budget |
| `time_overrun_months` | months | Predicted time overrun |

Both outputs are clipped to ≥ 0 (no negative overruns).

### Derived Metrics (computed in API layer)
- `cost_overrun_percentage` = (cost_overrun_crore / original_cost) × 100
- `time_overrun_percentage` = (time_overrun_months / time_delay_months) × 100 (when time_delay > 0)

## 4. Risk Classification (Provisional)

| Category | Criteria |
|---|---|
| **SAFE** (Green) | cost_overrun_percentage ≤ 5% AND time_overrun_months ≤ 3 |
| **RISKY** (Red) | cost_overrun_percentage > 15% OR time_overrun_months > 12 |
| **MODERATE** (Amber) | Everything else |

> [!NOTE]
> These thresholds are provisional and should be calibrated against domain expertise and historical project outcomes.

## 5. Critical Model Sanity Check & Bug Investigation

### The 35.98 Months Investigation
**Symptom Reported:**
- Test A: Petroleum, cost = ₹12,500 Cr, progress = 23%, delay = 36 months → Cost overrun ₹3492.85 Cr, Time overrun 35.98 months.
- Test B: Petroleum, cost = ₹1,200 Cr, progress = 50%, delay = 36 months → Cost overrun ₹249.69 Cr, Time overrun 35.98 months.

**Root Cause Analysis:**
1. **Feature Dominance in Time Overrun Model:**
   In the trained XGBoost model (`MultiOutputRegressor.estimators_[1]`), `Time_Delay_Months` accounts for **70.81%** of total split gain importance, followed by unmapped/sparse sector categories. For the Petroleum sector, `Physical_Progress` has only **0.0078** importance and `Original_Cost` has **0.0119** importance.
2. **Training Data Collinearity:**
   In `extracted_project_data.csv`, `Time_Delay_Months` and `Time_Overrun_Months` are identical across 100% of rows (correlation = 1.0, mean = 60.73, std = 57.83). Consequently, the XGBoost tree regressor learned that for any project with `Time_Delay_Months = 36`, the expected additional time overrun is closely anchored around ~35.98 months.
3. **Semantics Difference:**
   In the CLI and government forms, users sometimes treat the input as "planned duration" or "time given to project". However, the training feature is explicitly `Time_Delay_Months` (the schedule delay already accumulated). When delay = 36 months, an overrun near 36 months is the learned expectation of the model.
4. **Controlled Sensitivity Verification:**
   - Varying delay (0, 6, 12, 24, 36, 48): Time overrun scales monotonically from 2.41 months to 48.20 months.
   - Varying progress (10% to 90%) at delay=36: Time overrun varies between 35.81 and 36.03 months, while Cost Overrun varies significantly from ₹1,299 Cr down to ₹874 Cr.
   - Varying cost (₹500 to ₹50,000 Cr) at delay=36: Time overrun remains ~36.0 months, while Cost Overrun scales from ₹78 Cr up to ₹14,441 Cr.
5. **Finding:** The identical output (35.98 months) is not caused by variable leakage or a hardcoded default, but by the mathematical convergence of the tree model onto the heavily dominant `Time_Delay_Months` feature when fed the same delay (36 months).

## 6. Evaluation Metrics

Metrics stored in the model artifact (`metrics` key):
- **Cost Overrun**: R² = 0.9939, MAE = 108.78 (₹ Crore), RMSE = 317.02 (₹ Crore)
- **Time Overrun**: R² = 0.9998, MAE = 0.24 (months), RMSE = 0.71 (months)

## 7. Explainability

SHAP TreeExplainer is used for per-prediction feature importance:
- `explain_prediction.py` provides per-feature SHAP contributions
- Top risk drivers surfaced in prediction responses

## 8. Limitations & Audit Findings

1. **Synthetic time overrun target**: `Time_Delay_Months` in the extracted report dataset matches `Time_Overrun_Months` almost 1:1, creating a strong anchor where time overrun follows delay.
2. **Point estimates only**: No confidence intervals or empirical standard errors are generated by the model. Prediction ranges must not be fabricated.
3. **Sector mapping**: 7 canonical sectors supported. Unrecognized sector strings fall back to token overlap matching.

## 9. Integration Requirements

- Python 3.12+ with standard library HTTP microservice (`model/server.py`) or FastAPI (`model/api.py`).
- Java 21 Spring Boot backend invoking `http://localhost:8000/predict`.
- React frontend consuming `/api/predictions` with verified input schema.
