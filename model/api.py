"""FastAPI inference service for the SIH cost/time overrun prediction model."""

from __future__ import annotations

import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Ensure the model package is importable.  api.py lives at model/, so we add
# the *project root* (one level up) so that ``from model.src.predict import …``
# works, **and** we add ``model/src`` so the intra‑package ``from predict …``
# inside explain_prediction.py also resolves.
# ---------------------------------------------------------------------------
_MODEL_DIR = Path(__file__).resolve().parent            # …/model
_PROJECT_ROOT = _MODEL_DIR.parent                       # …/PREDICTION-MODEL
_SRC_DIR = _MODEL_DIR / "src"

for _p in (_PROJECT_ROOT, _SRC_DIR):
    _str = str(_p)
    if _str not in sys.path:
        sys.path.insert(0, _str)

from model.src.predict import predict_project_risk          # noqa: E402
from model.src.explain_prediction import explain_prediction  # noqa: E402

logger = logging.getLogger("uvicorn.error")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_VERSION = "1.0.0"
MODEL_PATH = _MODEL_DIR / "models" / "sih_cost_prediction_model.pkl"
TOP_K_DRIVERS = 5

# ---------------------------------------------------------------------------
# Global model state – populated in lifespan
# ---------------------------------------------------------------------------
_model_artifact: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    sector: str = Field(..., examples=["Power"])
    original_cost: float = Field(..., gt=0, description="Original cost in ₹ Crore")
    physical_progress: float = Field(..., ge=0, le=100, description="Physical progress 0‑100%")
    time_delay_months: float = Field(0.0, ge=0, description="Time delay in months")


class RiskDriver(BaseModel):
    feature: str
    contribution: float
    raw_value: float


class PredictionResponse(BaseModel):
    cost_overrun_crore: float
    time_overrun_months: float
    cost_overrun_percentage: float
    time_overrun_percentage: float
    risk_category: str
    risk_drivers: list[RiskDriver]
    model_version: str
    prediction_timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str


class ModelInfoResponse(BaseModel):
    model_version: str
    sector_aliases: list[str]
    target_names: list[str]
    metrics: dict[str, Any] | None


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------
def classify_risk(cost_overrun_pct: float, time_overrun_months: float) -> str:
    """Classify risk based on provisional thresholds.

    - SAFE:     cost_overrun_percentage <= 5 AND time_overrun_months <= 3
    - RISKY:    cost_overrun_percentage > 15 OR  time_overrun_months > 12
    - MODERATE: everything else
    """
    if cost_overrun_pct > 15.0 or time_overrun_months > 12.0:
        return "RISKY"
    if cost_overrun_pct <= 5.0 and time_overrun_months <= 3.0:
        return "SAFE"
    return "MODERATE"


# ---------------------------------------------------------------------------
# Lifespan – load model once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading model from %s …", MODEL_PATH)
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model artifact not found at {MODEL_PATH}")
    artifact = joblib.load(MODEL_PATH)
    if isinstance(artifact, dict):
        _model_artifact["model"] = artifact.get("model")
        _model_artifact["sector_aliases"] = artifact.get("sector_aliases", [])
        _model_artifact["target_names"] = artifact.get("target_names", [])
        _model_artifact["metrics"] = artifact.get("metrics")
    else:
        _model_artifact["model"] = artifact
        _model_artifact["sector_aliases"] = []
        _model_artifact["target_names"] = []
        _model_artifact["metrics"] = None
    logger.info("Model loaded successfully.")
    yield
    _model_artifact.clear()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SIH Cost & Time Overrun Prediction API",
    version=MODEL_VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=bool(_model_artifact.get("model")),
        model_version=MODEL_VERSION,
    )


@app.get("/model-info", response_model=ModelInfoResponse)
async def model_info():
    return ModelInfoResponse(
        model_version=MODEL_VERSION,
        sector_aliases=_model_artifact.get("sector_aliases", []),
        target_names=_model_artifact.get("target_names", []),
        metrics=_model_artifact.get("metrics"),
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(req: PredictionRequest):
    try:
        # ---- raw prediction ------------------------------------------------
        result = predict_project_risk(
            model_path=MODEL_PATH,
            sector=req.sector,
            original_cost=req.original_cost,
            physical_progress=req.physical_progress,
            time_delay_months=req.time_delay_months,
        )
        cost_overrun: float = result["cost_overrun_crore"]
        time_overrun: float = result["time_overrun_months"]

        # ---- derived percentages -------------------------------------------
        cost_overrun_pct = (cost_overrun / req.original_cost * 100.0) if req.original_cost else 0.0
        # time_overrun_percentage = time_overrun relative to time_delay_months
        time_overrun_pct = (
            (time_overrun / req.time_delay_months * 100.0)
            if req.time_delay_months
            else 0.0
        )

        # ---- risk category -------------------------------------------------
        risk_category = classify_risk(cost_overrun_pct, time_overrun)

        # ---- SHAP risk drivers ---------------------------------------------
        risk_drivers: list[RiskDriver] = []
        try:
            explanation = explain_prediction(
                model_path=MODEL_PATH,
                sector=req.sector,
                original_cost=req.original_cost,
                physical_progress=req.physical_progress,
                time_delay_months=req.time_delay_months,
            )
            # Merge cost and time feature importances, take top‑K by |contribution|
            all_features: list[dict[str, Any]] = []
            for target_key in ("cost_overrun", "time_overrun"):
                target_block = explanation.get("targets", {}).get(target_key, {})
                for item in target_block.get("feature_importance", []):
                    all_features.append(item)

            # Deduplicate by feature name keeping the entry with highest |contribution|
            seen: dict[str, dict[str, Any]] = {}
            for f in all_features:
                name = f["feature"]
                if name not in seen or abs(f["contribution"]) > abs(seen[name]["contribution"]):
                    seen[name] = f
            sorted_features = sorted(seen.values(), key=lambda x: abs(x["contribution"]), reverse=True)

            risk_drivers = [
                RiskDriver(
                    feature=f["feature"],
                    contribution=round(f["contribution"], 4),
                    raw_value=round(f["raw_value"], 4),
                )
                for f in sorted_features[:TOP_K_DRIVERS]
            ]
        except Exception as shap_err:
            logger.warning("SHAP explanation failed: %s", shap_err)

        return PredictionResponse(
            cost_overrun_crore=round(cost_overrun, 2),
            time_overrun_months=round(time_overrun, 2),
            cost_overrun_percentage=round(cost_overrun_pct, 2),
            time_overrun_percentage=round(time_overrun_pct, 2),
            risk_category=risk_category,
            risk_drivers=risk_drivers,
            model_version=MODEL_VERSION,
            prediction_timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Entrypoint for ``python api.py``
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
