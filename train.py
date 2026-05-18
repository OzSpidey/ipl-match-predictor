"""
IPL Match Winner Predictor — Model Training Pipeline
Trains Logistic Regression, Random Forest, XGBoost, LightGBM,
then builds a calibrated soft-voting ensemble. Uses time-based splits
to prevent leakage. Saves all artifacts to models/.
"""

import json
import warnings
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_predict
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, log_loss, roc_auc_score, confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from src.feature_engineering import FEATURE_COLS, build_features

warnings.filterwarnings("ignore")

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)
DATA_PATH  = Path("data/matches.csv")

TRAIN_CUTOFF = 2021   # seasons 2008-2020 for training
VAL_CUTOFF   = 2022   # season 2021 for validation
# test set: 2022-2024


def load_and_prepare() -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = build_features(df)

    X = df[FEATURE_COLS].values
    y = df["team1_won"].values
    seasons = df["season"].values

    train_mask = seasons < TRAIN_CUTOFF
    val_mask   = seasons == TRAIN_CUTOFF
    test_mask  = seasons >= VAL_CUTOFF

    return (
        df,
        X[train_mask], y[train_mask],
        X[val_mask],   y[val_mask],
        X[test_mask],  y[test_mask],
    )


def make_models():
    lr = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(C=0.5, max_iter=1000, random_state=42)),
    ])
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=5,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    xgb = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42, n_jobs=-1,
    )
    lgbm = LGBMClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        class_weight="balanced", random_state=42, n_jobs=-1,
        verbose=-1,
    )
    return {"lr": lr, "rf": rf, "xgb": xgb, "lgbm": lgbm}


def evaluate(name: str, model, X_val, y_val, X_test, y_test):
    metrics = {}
    for split, X, y in [("val", X_val, y_val), ("test", X_test, y_test)]:
        probs = model.predict_proba(X)[:, 1]
        preds = model.predict(X)
        metrics[split] = {
            "accuracy": round(float(accuracy_score(y, preds)), 4),
            "f1":       round(float(f1_score(y, preds)), 4),
            "roc_auc":  round(float(roc_auc_score(y, probs)), 4),
            "log_loss": round(float(log_loss(y, probs)), 4),
        }
    print(f"  {name:8s}  "
          f"val-acc={metrics['val']['accuracy']:.3f}  "
          f"test-acc={metrics['test']['accuracy']:.3f}  "
          f"auc={metrics['test']['roc_auc']:.3f}")
    return metrics


def get_feature_importance(model, feature_names: list[str]) -> dict:
    """Extract feature importances from tree-based models."""
    clf = model
    if hasattr(clf, "named_steps"):
        clf = clf.named_steps.get("clf", clf)
    if hasattr(clf, "calibrated_classifiers_"):
        clf = clf.calibrated_classifiers_[0].base_estimator
    if hasattr(clf, "estimators_"):  # VotingClassifier
        return {}

    imp = None
    if hasattr(clf, "feature_importances_"):
        imp = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        imp = np.abs(clf.coef_[0])

    if imp is None:
        return {}
    imp = imp / imp.sum()
    return {name: round(float(v), 4) for name, v in zip(feature_names, imp)}


def train():
    print("-- Loading & engineering features -------------------------")
    df, X_tr, y_tr, X_val, y_val, X_te, y_te = load_and_prepare()
    print(f"   Train={len(y_tr)}  Val={len(y_val)}  Test={len(y_te)}")

    base_models = make_models()
    all_metrics = {}
    trained = {}

    print("\n-- Training individual models ------------------------------")
    for name, mdl in base_models.items():
        # Calibrate on train+val combined with 5-fold CV
        X_tv_cal = np.vstack([X_tr, X_val])
        y_tv_cal = np.concatenate([y_tr, y_val])
        cal = CalibratedClassifierCV(mdl, method="sigmoid", cv=5)
        cal.fit(X_tv_cal, y_tv_cal)
        metrics = evaluate(name, cal, X_val, y_val, X_te, y_te)
        all_metrics[name] = metrics
        trained[name] = cal
        # Also keep a raw-fitted version for feature importance
        if name in ("xgb", "rf"):
            mdl.fit(X_tr, y_tr)
            base_models[name] = mdl
        joblib.dump(cal, MODELS_DIR / f"{name}.pkl")

    print("\n-- Building calibrated ensemble ----------------------------")
    # Soft-voting ensemble — re-fit on train+val combined
    X_tv = np.vstack([X_tr, X_val])
    y_tv = np.concatenate([y_tr, y_val])

    ensemble = VotingClassifier(
        estimators=[(k, v) for k, v in trained.items()],
        voting="soft", weights=[1, 2, 2, 2],   # down-weight LR
    )
    ensemble.fit(X_tv, y_tv)
    ens_metrics = evaluate("ensemble", ensemble, X_val, y_val, X_te, y_te)
    all_metrics["ensemble"] = ens_metrics
    joblib.dump(ensemble, MODELS_DIR / "ensemble.pkl")

    # Confusion matrix for the ensemble on test set
    preds_test = ensemble.predict(X_te)
    cm = confusion_matrix(y_te, preds_test).tolist()

    # Feature importance from XGBoost (best single model)
    xgb_base = base_models["xgb"]
    feat_imp = {}
    if hasattr(xgb_base, "feature_importances_"):
        raw = xgb_base.feature_importances_
        feat_imp = {name: round(float(v), 4) for name, v in zip(FEATURE_COLS, raw)}
        feat_imp = dict(sorted(feat_imp.items(), key=lambda x: -x[1]))

    # Save full match data + engineered features for the API
    df[FEATURE_COLS + ["team1", "team2", "venue", "season", "date", "winner", "team1_won"]].to_parquet(
        MODELS_DIR / "features.parquet", index=False
    )

    # Persist metadata
    metadata = {
        "metrics":          all_metrics,
        "feature_importance": feat_imp,
        "confusion_matrix": cm,
        "feature_cols":     FEATURE_COLS,
        "train_seasons":    f"2008-{TRAIN_CUTOFF - 1}",
        "test_seasons":     f"{VAL_CUTOFF}-2026",
        "total_matches":    len(df),
    }
    (MODELS_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

    print(f"\n-- Results saved to {MODELS_DIR}/ -------------------------")
    print(f"   Ensemble test accuracy : {ens_metrics['test']['accuracy']:.3f}")
    print(f"   Ensemble test AUC      : {ens_metrics['test']['roc_auc']:.3f}")
    print("\nTop-5 features (XGBoost importance):")
    for k, v in list(feat_imp.items())[:5]:
        print(f"   {k:35s} {v:.4f}")


if __name__ == "__main__":
    train()
