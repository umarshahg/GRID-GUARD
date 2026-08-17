import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest

def train_isolation_forest(X_train, y_train):
    print("🌲 Training Isolation Forest...")
    # Train on normal traffic only
    X_normal = X_train[y_train == 0]
    print(f"   Training on {len(X_normal):,} normal traffic samples")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_normal)
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/isolation_forest.pkl")
    print("   ✅ Saved → models/isolation_forest.pkl")
    return model

def score_isolation_forest(model, X):
    raw = -model.decision_function(X)
    return (raw - raw.min()) / (raw.max() - raw.min())
