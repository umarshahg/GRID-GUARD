import numpy as np
import pandas as pd

# Weights from your SDS document
WEIGHTS = {
    "isolation_forest": 0.20,
    "one_class_svm":    0.15,
    "random_forest":    0.30,
    "xgboost":          0.35
}

def compute_risk_score(if_score, svm_score, rf_score, xgb_score):
    """
    Combines all four model scores into one risk score 0-100%.
    
    Formula from SDS:
    risk = (IF × 0.20) + (SVM × 0.15) + (RF × 0.30) + (XGB × 0.35)
    Multiply by 100 to get percentage.
    """
    risk = (
        if_score  * WEIGHTS["isolation_forest"] +
        svm_score * WEIGHTS["one_class_svm"]    +
        rf_score  * WEIGHTS["random_forest"]    +
        xgb_score * WEIGHTS["xgboost"]
    )
    return risk * 100  # convert to 0-100%

def get_response_tier(risk_score):
    """
    Maps risk score to graduated response tier.
    Exactly as defined in SRS and SDS.
    """
    if risk_score < 60:
        return 1, "LOG ONLY"
    elif risk_score < 80:
        return 2, "ALERT — Notify Operator"
    elif risk_score < 95:
        return 3, "RATE LIMIT — Block Suspicious Commands"
    else:
        return 4, "FULL SANDBOX ISOLATION"

def run_ensemble(if_scores, svm_scores, rf_scores, xgb_scores):
    """
    Run ensemble on arrays of scores.
    Returns DataFrame with individual scores, risk score, tier.
    """
    results = pd.DataFrame({
        "if_score":   if_scores,
        "svm_score":  svm_scores,
        "rf_score":   rf_scores,
        "xgb_score":  xgb_scores,
    })

    results["risk_score"] = compute_risk_score(
        if_scores, svm_scores, rf_scores, xgb_scores
    )

    tiers = [get_response_tier(s) for s in results["risk_score"]]
    results["tier"]   = [t[0] for t in tiers]
    results["action"] = [t[1] for t in tiers]

    return results

if __name__ == "__main__":
    # Quick test with dummy scores
    test = run_ensemble(
        if_scores  = np.array([0.1, 0.9, 0.5, 0.8]),
        svm_scores = np.array([0.1, 0.8, 0.4, 0.9]),
        rf_scores  = np.array([0.0, 0.95, 0.6, 0.7]),
        xgb_scores = np.array([0.0, 0.98, 0.55, 0.85])
    )
    print(test.to_string())
