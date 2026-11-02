"""Lightweight, dependency-free HTTP microservice for the SIH Prediction Model.
Compatible with standard library http.server, responding to Spring Boot and Frontend.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add project root and model/src to sys.path
_MODEL_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODEL_DIR.parent
_SRC_DIR = _MODEL_DIR / "src"

for _p in (_PROJECT_ROOT, _SRC_DIR):
    _str = str(_p)
    if _str not in sys.path:
        sys.path.insert(0, _str)

from model.src.predict import predict_project_risk
from model.src.explain_prediction import explain_prediction

MODEL_VERSION = "1.0.0"
MODEL_PATH = _MODEL_DIR / "models" / "sih_cost_prediction_model.pkl"
PORT = 8000

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("model-server")


def classify_risk(cost_overrun_pct: float, time_overrun_months: float) -> str:
    """Classify risk using standard thresholds:
    - SAFE:     cost_overrun_percentage <= 5 AND time_overrun_months <= 3
    - RISKY:    cost_overrun_percentage > 15 OR  time_overrun_months > 12
    - MODERATE: everything else
    """
    if cost_overrun_pct > 15.0 or time_overrun_months > 12.0:
        return "RISKY"
    if cost_overrun_pct <= 5.0 and time_overrun_months <= 3.0:
        return "SAFE"
    return "MODERATE"


class PredictionRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/health"):
            self._send_json(200, {
                "status": "healthy",
                "model_loaded": MODEL_PATH.exists(),
                "model_version": MODEL_VERSION
            })
        elif self.path == "/info":
            self._send_json(200, {
                "model_version": MODEL_VERSION,
                "model_path": str(MODEL_PATH),
                "features": ["Sector", "Original_Cost", "Physical_Progress", "Time_Delay_Months"],
                "targets": ["Overrun_Amount", "Time_Overrun_Months"]
            })
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        if self.path == "/predict":
            try:
                length_str = self.headers.get("Content-Length")
                logger.info("Headers: %s", dict(self.headers))
                if length_str and int(length_str) > 0:
                    body = self.rfile.read(int(length_str)).decode("utf-8")
                elif self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                    chunks = []
                    while True:
                        line = self.rfile.readline().strip()
                        if not line:
                            break
                        chunk_len = int(line, 16)
                        if chunk_len == 0:
                            self.rfile.readline() # consume trailing CRLF
                            break
                        chunk_data = self.rfile.read(chunk_len)
                        chunks.append(chunk_data)
                        self.rfile.readline() # consume trailing CRLF
                    body = b"".join(chunks).decode("utf-8")
                else:
                    body = ""
                logger.info("Body received: %r", body)
                payload = json.loads(body)

                sector = str(payload.get("sector", "Road Transport & Highways"))
                original_cost = float(payload.get("original_cost", 0.0))
                physical_progress = float(payload.get("physical_progress", 0.0))
                time_delay = float(payload.get("time_delay_months", 0.0))

                if original_cost <= 0:
                    self._send_json(400, {"error": "original_cost must be > 0"})
                    return

                # Execute XGBoost prediction
                pred = predict_project_risk(
                    MODEL_PATH,
                    sector=sector,
                    original_cost=original_cost,
                    physical_progress=physical_progress,
                    time_delay_months=time_delay
                )

                cost_overrun = pred["cost_overrun_crore"]
                time_overrun = pred["time_overrun_months"]
                cost_overrun_pct = round((cost_overrun / original_cost) * 100.0, 2)
                time_overrun_pct = round((time_overrun / time_delay) * 100.0, 2) if time_delay > 0 else 0.0
                risk_cat = classify_risk(cost_overrun_pct, time_overrun)

                # Compute SHAP explainability drivers if possible
                risk_drivers = []
                try:
                    exp = explain_prediction(
                        MODEL_PATH,
                        sector=sector,
                        original_cost=original_cost,
                        physical_progress=physical_progress,
                        time_delay_months=time_delay
                    )
                    cost_drivers = exp.get("targets", {}).get("cost_overrun", {}).get("top_drivers", [])
                    for d in cost_drivers[:5]:
                        risk_drivers.append({
                            "feature": d["feature"],
                            "contribution": d["contribution"],
                            "raw_value": d["raw_value"]
                        })
                except Exception as ex:
                    logger.warning(f"SHAP explanation failed: {ex}")

                response_payload = {
                    "cost_overrun_crore": round(cost_overrun, 2),
                    "time_overrun_months": int(round(time_overrun)),
                    "cost_overrun_percentage": cost_overrun_pct,
                    "time_overrun_percentage": time_overrun_pct,
                    "risk_category": risk_cat,
                    "risk_drivers": risk_drivers,
                    "model_version": MODEL_VERSION,
                    "prediction_timestamp": datetime.now(timezone.utc).isoformat()
                }

                self._send_json(200, response_payload)

            except Exception as e:
                logger.error(f"Prediction error: {e}", exc_info=True)
                self._send_json(500, {"error": "Prediction execution failed", "details": str(e)})
        else:
            self._send_json(404, {"error": "Endpoint not found"})


def run_server():
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, PredictionRequestHandler)
    logger.info(f"GovProject Model Service running on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        logger.info("Model server stopped.")


if __name__ == "__main__":
    run_server()

