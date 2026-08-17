import pandas as pd
import numpy as np
import joblib
import os
from xgboost import XGBClassifier

def train_xgboost(X_train, y_train, X_val, y_val):
    """
    XGBoost is SUPERVISED.
    Best performing model in the ensemble (35% weight).
    Uses gradient boosting — each tree corrects errors of previous ones.
    Uses validation set for early stopping to prevent overfitting.
    """
    print("⚡ Training XGBoost...")
    print(f"   Training on {len(X_train):,} samples")

    model = XGBClassifier(
        n_estimators=500,          # max trees
        learning_rate=0.05,        # step size
        max_depth=8,
        subsample=0.8,             # use 80% of data per tree
        colsample_bytree=0.8,      # use 80% of features per tree
        scale_pos_weight=1,        # already balanced by SMOTE
        use_label_encoder=False,
        eval_metric='logloss',
        early_stopping_rounds=20,  # stop if no improvement for 20 rounds
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50  # print progress every 50 rounds
    )

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/xgboost_model.pkl")
    print("   ✅ Saved → models/xgboost_model.pkl")
    return model

def score_xgboost(model, X):
    """
    Returns probability of botnet class (0 to 1).
    """
    return model.predict_proba(X)[:, 1]

if __name__ == "__main__":
    X_train = pd.read_parquet("data/train_features.parquet")
    y_train = pd.read_parquet("data/train_labels.parquet")["label"]
    X_val   = pd.read_parquet("data/val_features.parquet")
    y_val   = pd.read_parquet("data/val_labels.parquet")["label"]
    model   = train_xgboost(X_train, y_train, X_val, y_val)
    scores  = score_xgboost(model, X_train.head(5))
    print(f"   Sample scores: {scores.round(3)}")
