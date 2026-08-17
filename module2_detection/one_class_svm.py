import pandas as pd
import numpy as np
import joblib
import os
from sklearn.svm import OneClassSVM

def train_one_class_svm(X_train, y_train):
    print("🔵 Training One-Class SVM...")
    X_normal = X_train[y_train == 0]
    sample_size = min(20000, len(X_normal))
    X_sample = X_normal.sample(n=sample_size, random_state=42)
    print(f"   Training on {sample_size:,} normal samples (sampled for speed)")
    model = OneClassSVM(kernel='rbf', gamma='scale', nu=0.05)
    model.fit(X_sample)
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/one_class_svm.pkl")
    print("   ✅ Saved → models/one_class_svm.pkl")
    return model

def score_one_class_svm(model, X):
    raw = -model.decision_function(X)
    return (raw - raw.min()) / (raw.max() - raw.min())
