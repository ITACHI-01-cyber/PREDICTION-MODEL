import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from predict import predict_project_risk

model_path = Path(__file__).resolve().parent.parent / "models" / "sih_cost_prediction_model.pkl"

print("--- Delay Sensitivity (Cost=5000, Prog=50) ---")
for d in [0, 6, 12, 24, 36, 48]:
    res = predict_project_risk(model_path, "Petroleum", 5000, 50, d)
    print(f"delay={d:2d} -> time_overrun={res['time_overrun_months']:.4f}")

print("\n--- Progress Sensitivity (Cost=5000, Delay=36) ---")
for p in [10, 30, 50, 70, 90]:
    res = predict_project_risk(model_path, "Petroleum", 5000, p, 36)
    print(f"progress={p:2d}% -> time_overrun={res['time_overrun_months']:.4f}, cost_overrun={res['cost_overrun_crore']:.2f}")

print("\n--- Cost Sensitivity (Prog=50, Delay=36) ---")
for c in [500, 2000, 10000, 50000]:
    res = predict_project_risk(model_path, "Petroleum", c, 50, 36)
    print(f"cost={c:5d} -> time_overrun={res['time_overrun_months']:.4f}, cost_overrun={res['cost_overrun_crore']:.2f}")

print("\n--- Test A & B Verification ---")
test_a = predict_project_risk(model_path, "Petroleum", 12500, 23, 36)
test_b = predict_project_risk(model_path, "Petroleum", 1200, 50, 36)
print("Test A:", test_a)
print("Test B:", test_b)

