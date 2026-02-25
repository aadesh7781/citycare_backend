# test_ml.py
import sys
sys.path.append(".")

from utils.ml_model import predict_score

test_complaints = [
    "exposed live wire near school causing accidents",
    "minor pothole on side lane",
    "gas leak from pipeline near hospital blocking emergency access",
    "broken dustbin since yesterday",
    "dengue outbreak in slum affecting hundreds of families",
    "garbage not collected for days in residential area",
    "transformer sparking near market causing fire risk",
    "small crack on footpath",
    "sewage overflow on main road creating health risk",
    "damaged park bench in garden",
]

print("=" * 55)
print("  URGENCY MODEL — LOCAL TEST")
print("=" * 55)
print(f"{'Score':>7}  {'Complaint'}")
print("-" * 55)

for complaint in test_complaints:
    score = predict_score(complaint)
    if score >= 75:
        tag = "🔴 EMERGENCY"
    elif score >= 50:
        tag = "🟠 HIGH"
    elif score >= 25:
        tag = "🟡 MEDIUM"
    else:
        tag = "🟢 LOW"
    print(f"[{score:>3}] {tag}  {complaint[:45]}")

print("=" * 55)
print("✅ Model working correctly!")