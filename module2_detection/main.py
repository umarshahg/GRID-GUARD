import pandas as pd
import numpy as np
import joblib
import json

from isolation_forest import train_isolation_forest, score_isolation_forest
from one_class_svm     import train_one_class_svm,    score_one_class_svm
from random_forest     import train_random_forest,     score_random_forest
from xgboost_model     import train_xgboost,           score_xgboost
from ensemble          import run_ensemble
from evaluator         import evaluate, plot_risk_distribution

print("="*55)
print("  GRID GUARD — Module 2: Botnet Detection Engine")
print("  Dataset: BoTNeTIoT-L01-v2")
print("="*55)

# ── Load datasets ──
print("\n📂 Loading datasets...")
X_train = pd.read_parquet("data/train_features.parquet")
y_train = pd.read_parquet("data/train_labels.parquet").iloc[:,0]
X_val   = pd.read_parquet("data/val_features.parquet")
y_val   = pd.read_parquet("data/val_labels.parquet").iloc[:,0]
X_test  = pd.read_parquet("data/test_features.parquet")
y_test  = pd.read_parquet("data/test_labels.parquet").iloc[:,0]

# NOTE: StandardScaler used — do NOT clip values
print(f"   Train : {len(X_train):,} | Normal={int((y_train==0).sum()):,} Botnet={int((y_train==1).sum()):,}")
print(f"   Val   : {len(X_val):,} | Normal={int((y_val==0).sum()):,} Botnet={int((y_val==1).sum()):,}")
print(f"   Test  : {len(X_test):,} | Normal={int((y_test==0).sum()):,} Botnet={int((y_test==1).sum()):,}")
print(f"   Features: {X_train.shape[1]}")

# ── Train all 4 models ──
print("\n🤖 Training Models...")
if_model  = train_isolation_forest(X_train, y_train)
svm_model = train_one_class_svm(X_train, y_train)
rf_model  = train_random_forest(X_train, y_train)
xgb_model = train_xgboost(X_train, y_train, X_val, y_val)

# ── Score test set ──
print("\n📊 Scoring test set...")
if_scores  = score_isolation_forest(if_model,  X_test)
svm_scores = score_one_class_svm(svm_model, X_test)
rf_scores  = score_random_forest(rf_model,  X_test)
xgb_scores = score_xgboost(xgb_model, X_test)

# ── Ensemble ──
print("\n⚖️  Running weighted ensemble...")
results = run_ensemble(if_scores, svm_scores, rf_scores, xgb_scores)
risk_scores = results["risk_score"].values

# ── Evaluate ──
metrics = evaluate(y_test.values, risk_scores)

# ── Plot ──
plot_risk_distribution(risk_scores, y_test.values)

# ── Sample predictions ──
print("\n🔍 Sample predictions (first 10 test flows):")
sample = results.head(10).copy()
sample["actual"] = y_test.values[:10]
sample["actual_label"] = sample["actual"].map({0:"Normal", 1:"Botnet"})
print(sample[["risk_score","tier","action","actual_label"]].to_string())

print("\n✅ Module 2 complete. All models saved in models/ folder.")
