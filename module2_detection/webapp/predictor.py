# webapp/predictor.py
# ─────────────────────────────────────────────────────────────
# Loads all 4 trained models and runs the weighted ensemble.
# This is the bridge between Flask API and Module 2 ML models.
# ─────────────────────────────────────────────────────────────

import sys
import os
import numpy as np
import pandas as pd
import joblib
import json

# Add parent directory to path so we can import ensemble.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ensemble import compute_risk_score, get_response_tier

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR  = os.path.join(BASE_DIR, 'models')
DATA_DIR    = os.path.join(BASE_DIR, 'data')

# ── Ensemble Weights (from SDS) ────────────────────────────────
WEIGHTS = {
    "isolation_forest": 0.20,
    "one_class_svm":    0.15,
    "random_forest":    0.30,
    "xgboost":          0.35,
}


class GridGuardPredictor:
    """
    Loads all 4 trained models once at startup.
    Exposes predict() for single or batch flow scoring.
    Exposes get_summary() for dashboard statistics.
    """

    def __init__(self):
        self.if_model  = None
        self.svm_model = None
        self.rf_model  = None
        self.xgb_model = None
        self.scaler    = None
        self.features  = None
        self.loaded    = False
        self._load_models()
        self._load_test_data()

    # ── Model Loading ──────────────────────────────────────────
    def _load_models(self):
        try:
            print("[Predictor] Loading models...")

            self.if_model  = joblib.load(os.path.join(MODELS_DIR, 'isolation_forest.pkl'))
            print("[Predictor] ✅ Isolation Forest loaded")

            self.svm_model = joblib.load(os.path.join(MODELS_DIR, 'one_class_svm.pkl'))
            print("[Predictor] ✅ One-Class SVM loaded")

            self.rf_model  = joblib.load(os.path.join(MODELS_DIR, 'random_forest.pkl'))
            print("[Predictor] ✅ Random Forest loaded")

            self.xgb_model = joblib.load(os.path.join(MODELS_DIR, 'xgboost_model.pkl'))
            print("[Predictor] ✅ XGBoost loaded")

            self.scaler    = joblib.load(os.path.join(DATA_DIR, 'scaler.joblib'))
            print("[Predictor] ✅ Scaler loaded")

            with open(os.path.join(DATA_DIR, 'feature_list.json')) as f:
                self.features = json.load(f)
            print(f"[Predictor] ✅ Features loaded — {len(self.features)} features")

            self.loaded = True
            print("[Predictor] ✅ All models ready")

        except Exception as e:
            print(f"[Predictor] ❌ Error loading models: {e}")
            self.loaded = False

    # ── Test Data Loading ──────────────────────────────────────
    def _load_test_data(self):
        try:
            self.X_test = pd.read_parquet(
                os.path.join(DATA_DIR, 'test_features.parquet')
            )
            self.y_test = pd.read_parquet(
                os.path.join(DATA_DIR, 'test_labels.parquet')
            ).iloc[:, 0]
            print(f"[Predictor] ✅ Test data loaded — {len(self.X_test):,} rows")
        except Exception as e:
            print(f"[Predictor] ⚠️  Could not load test data: {e}")
            self.X_test = None
            self.y_test = None

    # ── Core Scoring ───────────────────────────────────────────
    def _score_sample(self, X):
        """
        Runs all 4 models on X and returns ensemble risk score.
        X must be a DataFrame with correct feature columns.
        """
        # Isolation Forest score
        raw_if  = -self.if_model.decision_function(X)
        if_min, if_max = raw_if.min(), raw_if.max()
        if_scores = (raw_if - if_min) / (if_max - if_min + 1e-9)

        # One-Class SVM score
        raw_svm  = -self.svm_model.decision_function(X)
        svm_min, svm_max = raw_svm.min(), raw_svm.max()
        svm_scores = (raw_svm - svm_min) / (svm_max - svm_min + 1e-9)

        # Random Forest score
        rf_scores = self.rf_model.predict_proba(X)[:, 1]

        # XGBoost score
        xgb_scores = self.xgb_model.predict_proba(X)[:, 1]

        # Weighted ensemble
        risk = (
            if_scores  * WEIGHTS["isolation_forest"] +
            svm_scores * WEIGHTS["one_class_svm"]    +
            rf_scores  * WEIGHTS["random_forest"]    +
            xgb_scores * WEIGHTS["xgboost"]
        ) * 100

        return risk, rf_scores, if_scores

    # ── Public: Predict on random test sample ─────────────────
    def predict_sample(self, n=50):
        """
        Scores n random flows from test set.
        Returns list of dicts for frontend table display.
        """
        if not self.loaded or self.X_test is None:
            return []

        sample = self.X_test.sample(n=min(n, len(self.X_test)), random_state=42)
        labels = self.y_test.loc[sample.index].values

        risk_scores, rf_scores, if_scores = self._score_sample(sample)

        results = []
        for i in range(len(sample)):
            tier, action = get_response_tier(risk_scores[i])
            results.append({
                "flow_id":    f"FLOW-{i+1:04d}",
                "risk_score": round(float(risk_scores[i]), 2),
                "tier":       int(tier),
                "action":     action,
                "actual":     "Botnet" if labels[i] == 1 else "Normal",
                "predicted":  "Botnet" if risk_scores[i] >= 50 else "Normal",
                "rf_score":   round(float(rf_scores[i]) * 100, 2),
                "if_score":   round(float(if_scores[i]) * 100, 2),
            })

        return results

    # ── Public: Full test set summary stats ───────────────────
    def get_summary(self):
        """
        Returns dashboard summary statistics computed from
        the full test set using all 4 models.
        """
        if not self.loaded or self.X_test is None:
            return self._empty_summary()

        try:
            risk_scores, rf_scores, if_scores = self._score_sample(self.X_test)
            y = self.y_test.values
            predicted = (risk_scores >= 50).astype(int)

            # Confusion matrix
            tn = int(((predicted == 0) & (y == 0)).sum())
            fp = int(((predicted == 1) & (y == 0)).sum())
            fn = int(((predicted == 0) & (y == 1)).sum())
            tp = int(((predicted == 1) & (y == 1)).sum())

            total       = len(y)
            total_bot   = int((y == 1).sum())
            total_norm  = int((y == 0).sum())
            accuracy    = round((tp + tn) / total * 100, 2)
            det_rate    = round(tp / (tp + fn) * 100, 2) if (tp + fn) > 0 else 0
            fpr         = round(fp / (fp + tn) * 100, 2) if (fp + tn) > 0 else 0
            f1          = round(2*tp / (2*tp + fp + fn) * 100, 2) if (2*tp+fp+fn) > 0 else 0

            # Tier distribution
            tiers = [get_response_tier(s)[0] for s in risk_scores]
            tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            for t in tiers:
                tier_counts[t] += 1

            # Risk score histogram (20 bins)
            hist, bin_edges = np.histogram(risk_scores, bins=20, range=(0, 100))
            histogram = {
                "labels": [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}"
                           for i in range(len(hist))],
                "values": hist.tolist()
            }

            # Feature importance from RF
            importance = {}
            if hasattr(self.rf_model, 'feature_importances_'):
                imp = self.rf_model.feature_importances_
                sorted_idx = np.argsort(imp)[::-1][:7]
                importance = {
                    "features": [self.features[i] for i in sorted_idx],
                    "scores":   [round(float(imp[i]) * 100, 2) for i in sorted_idx]
                }

            # Anomaly score over time (simulate timeline using test rows)
            timeline_n  = 60
            step        = max(1, len(risk_scores) // timeline_n)
            timeline    = [round(float(s), 2) for s in risk_scores[::step][:timeline_n]]

            return {
                "status":        "online",
                "total_flows":   total,
                "total_normal":  total_norm,
                "total_botnet":  total_bot,
                "accuracy":      accuracy,
                "detection_rate":det_rate,
                "fpr":           fpr,
                "f1_score":      f1,
                "tp": tp, "tn": tn, "fp": fp, "fn": fn,
                "tier_counts":   tier_counts,
                "histogram":     histogram,
                "feature_importance": importance,
                "timeline":      timeline,
                "models_loaded": {
                    "isolation_forest": True,
                    "one_class_svm":    True,
                    "random_forest":    True,
                    "xgboost":          True,
                }
            }

        except Exception as e:
            print(f"[Predictor] ❌ Error in get_summary: {e}")
            return self._empty_summary()

    # ── Public: Live scan (simulate single meter scoring) ─────
    def scan_meter(self, meter_id=None):
        """
        Picks one random test flow and scores it.
        Simulates scanning a single smart meter.
        """
        if not self.loaded or self.X_test is None:
            return {}

        row    = self.X_test.sample(n=1)
        label  = int(self.y_test.loc[row.index].values[0])
        risk_scores, rf_scores, if_scores = self._score_sample(row)

        risk  = float(risk_scores[0])
        tier, action = get_response_tier(risk)

        return {
            "meter_id":   meter_id or f"SM-{np.random.randint(1000,9999)}",
            "risk_score": round(risk, 2),
            "tier":       tier,
            "action":     action,
            "status":     "Botnet" if risk >= 50 else "Normal",
            "rf_score":   round(float(rf_scores[0]) * 100, 2),
            "if_score":   round(float(if_scores[0]) * 100, 2),
            "actual":     "Botnet" if label == 1 else "Normal",
        }

    # ── Public: Traffic stats for Traffic Monitor page ────────
    def get_traffic_stats(self):
        """
        Returns traffic monitoring statistics for Traffic Monitor page.
        """
        if not self.loaded or self.X_test is None:
            return {}

        risk_scores, _, _ = self._score_sample(self.X_test)
        y = self.y_test.values

        normal_scores = risk_scores[y == 0]
        botnet_scores = risk_scores[y == 1]

        # Protocol distribution (simulated from feature weights)
        protocol_timeline = []
        chunk = max(1, len(risk_scores) // 30)
        for i in range(0, len(risk_scores), chunk):
            chunk_scores = risk_scores[i:i+chunk]
            protocol_timeline.append({
                "time":   f"{i//chunk:02d}:00",
                "dlms":   int(len(chunk_scores) * 0.6),
                "mqtt":   int(len(chunk_scores) * 0.4),
            })

        return {
            "total_flows":        len(risk_scores),
            "normal_flows":       int((y == 0).sum()),
            "botnet_flows":       int((y == 1).sum()),
            "normal_mean_risk":   round(float(normal_scores.mean()), 2),
            "botnet_mean_risk":   round(float(botnet_scores.mean()), 2),
            "protocol_timeline":  protocol_timeline[:30],
            "feature_names":      self.features,
        }

    # ── Fallback empty summary ─────────────────────────────────
    def _empty_summary(self):
        return {
            "status":         "offline",
            "total_flows":    0,
            "total_normal":   0,
            "total_botnet":   0,
            "accuracy":       0,
            "detection_rate": 0,
            "fpr":            0,
            "f1_score":       0,
            "tp": 0, "tn": 0, "fp": 0, "fn": 0,
            "tier_counts":    {1: 0, 2: 0, 3: 0, 4: 0},
            "histogram":      {"labels": [], "values": []},
            "feature_importance": {"features": [], "scores": []},
            "timeline":       [],
            "models_loaded":  {
                "isolation_forest": False,
                "one_class_svm":    False,
                "random_forest":    False,
                "xgboost":          False,
            }
        }


# ── Singleton instance ─────────────────────────────────────────
# Created once when Flask starts, shared across all requests
predictor = GridGuardPredictor()
