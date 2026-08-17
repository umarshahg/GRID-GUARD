import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier

def train_random_forest(X_train, y_train):
    """
    Random Forest is SUPERVISED.
    Trained on FULL dataset (both normal and botnet).
    Builds 200 decision trees and votes on each prediction.
    """
    print("🌳 Training Random Forest...")
    print(f"   Training on {len(X_train):,} samples")

    model = RandomForestClassifier(
        n_estimators=200,      # 200 decision trees
        max_depth=20,          # max tree depth
        min_samples_split=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/random_forest.pkl")
    print("   ✅ Saved → models/random_forest.pkl")

    # Print top 5 most important features
    importances = pd.Series(
        model.feature_importances_,
        index=X_train.columns
    ).sort_values(ascending=False)
    print("   Top 5 important features:")
    for feat, score in importances.head(5).items():
        print(f"     {feat}: {score:.4f}")

    return model

def score_random_forest(model, X):
    """
    Returns probability of botnet class (0 to 1).
    """
    return model.predict_proba(X)[:, 1]

if __name__ == "__main__":
    X_train = pd.read_parquet("data/train_features.parquet")
    y_train = pd.read_parquet("data/train_labels.parquet")["label"]
    model = train_random_forest(X_train, y_train)
    scores = score_random_forest(model, X_train.head(5))
    print(f"   Sample scores: {scores.round(3)}")
