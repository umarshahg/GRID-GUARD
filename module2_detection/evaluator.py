import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report
)

def evaluate(y_true, risk_scores, threshold=50.0):
    """
    Evaluates ensemble performance on test set.
    Converts risk scores to binary predictions using threshold.
    Risk >= threshold → predicted botnet (1)
    Risk <  threshold → predicted normal (0)
    """
    y_pred = (risk_scores >= threshold).astype(int)

    accuracy = accuracy_score(y_true, y_pred)
    f1       = f1_score(y_true, y_pred)
    auc      = roc_auc_score(y_true, risk_scores / 100)
    cm       = confusion_matrix(y_true, y_pred)

    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn)   # False Positive Rate
    tpr = tp / (tp + fn)   # True Positive Rate (Detection Rate)

    print("\n" + "="*50)
    print("       GRID GUARD — Module 2 Evaluation")
    print("="*50)
    print(f"  Accuracy          : {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  Detection Rate    : {tpr:.4f}  (Target: >0.95)")
    print(f"  False Positive Rate: {fpr:.4f} (Target: <0.02)")
    print(f"  F1 Score          : {f1:.4f}  (Target: >0.95)")
    print(f"  AUC-ROC           : {auc:.4f}  (Target: >0.97)")
    print("="*50)
    print("\nConfusion Matrix:")
    print(f"  True Negatives  (Normal  → Normal) : {tn:,}")
    print(f"  False Positives (Normal  → Botnet) : {fp:,}")
    print(f"  False Negatives (Botnet  → Normal) : {fn:,}")
    print(f"  True Positives  (Botnet  → Botnet) : {tp:,}")
    print("="*50)

    # Check targets
    print("\n  Target Check:")
    print(f"  Detection Rate >95% : {'✅ PASS' if tpr > 0.95 else '❌ FAIL'}")
    print(f"  FPR < 8%            : {'✅ PASS' if fpr < 0.08 else '❌ FAIL'}")
    print(f"  F1 > 0.85           : {'✅ PASS' if f1  > 0.95 else '❌ FAIL'}")
    print(f"  AUC > 0.90          : {'✅ PASS' if auc > 0.97 else '❌ FAIL'}")

    return {
        "accuracy": accuracy,
        "detection_rate": tpr,
        "fpr": fpr,
        "f1": f1,
        "auc": auc
    }

def plot_risk_distribution(risk_scores, y_true):
    """
    Plots risk score distribution for normal vs botnet traffic.
    """
    normal_scores = risk_scores[y_true == 0]
    botnet_scores = risk_scores[y_true == 1]

    plt.figure(figsize=(10, 5))
    plt.hist(normal_scores, bins=50, alpha=0.6,
             color='green', label='Normal Traffic')
    plt.hist(botnet_scores, bins=50, alpha=0.6,
             color='red',   label='Botnet Traffic')
    plt.axvline(x=60, color='orange', linestyle='--', label='Alert threshold (60%)')
    plt.axvline(x=95, color='red',    linestyle='--', label='Isolation threshold (95%)')
    plt.xlabel('Risk Score (%)')
    plt.ylabel('Number of Flows')
    plt.title('GRID GUARD — Risk Score Distribution')
    plt.legend()
    plt.tight_layout()
    plt.savefig("models/risk_distribution.png")
    plt.show()
    print("   📊 Plot saved → models/risk_distribution.png")
