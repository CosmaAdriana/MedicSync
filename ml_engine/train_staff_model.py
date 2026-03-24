"""
MedicSync — ML Staff Prediction Model Training
Trains a RandomForestRegressor on the `daily_patient_flow` historical data
to predict the number of patients (and therefore nurses needed) for a given day.

Features:  month, day_of_week, weather_temp, is_holiday, is_epidemic, department_id
Target:    patient_count

"""

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Path setup — allow importing from backend/app
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

# Change working directory to backend/ so the relative SQLite URL resolves correctly
os.chdir(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from app.database import SessionLocal
from app.models import DailyPatientFlow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(SCRIPT_DIR, "staff_model.joblib")
PATIENTS_PER_NURSE = 4  # Ratio used to compute recommended nurses


def load_data() -> pd.DataFrame:
    """Load all DailyPatientFlow rows into a pandas DataFrame."""
    db = SessionLocal()
    try:
        rows = db.query(DailyPatientFlow).all()
        if not rows:
            print("ERROR: Tabelul `daily_patient_flow` este gol. Rulează mai întâi scriptul de generare date.")
            sys.exit(1)

        data = [
            {
                "date": r.date,
                "department_id": r.department_id,
                "patient_count": r.patient_count,
                "weather_temp": r.weather_temp,
                "is_holiday": int(r.is_holiday),
                "is_epidemic": int(r.is_epidemic),
            }
            for r in rows
        ]
        return pd.DataFrame(data)
    finally:
        db.close()


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Extract calendar features from the date column."""
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek  # 0=Monday ... 6=Sunday
    return df


def train():
    """Full training pipeline: load → engineer → train → evaluate → save."""
    print("=" * 60)
    print("  MedicSync — ML Staff Prediction Training")
    print("=" * 60)

    # 1. Load data
    print("\n[1/4] Se încarcă datele din baza de date...")
    df = load_data()
    print(f"      → {len(df)} înregistrări încărcate.")

    # 2. Feature engineering
    print("[2/4] Se pregătesc feature-urile...")
    df = feature_engineering(df)

    feature_cols = ["month", "day_of_week", "weather_temp", "is_holiday", "is_epidemic", "department_id"]
    X = df[feature_cols]
    y = df["patient_count"]

    # Handle missing weather_temp
    X = X.fillna(X.mean())

    # 3. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"      → Train: {len(X_train)} | Test: {len(X_test)}")

    # 4. Train model
    print("[3/4] Se antrenează RandomForestRegressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n      Metrici pe setul de test:")
    print(f"        MAE  = {mae:.2f} pacienți")
    print(f"        R²   = {r2:.4f}")

    # Feature importance
    importances = dict(zip(feature_cols, model.feature_importances_))
    print(f"\n      Importanța feature-urilor:")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"        {feat:15s} → {imp:.4f}")

    # 6. Save model
    print(f"\n[4/4] Se salvează modelul în: {MODEL_PATH}")
    joblib.dump(
        {
            "model": model,
            "feature_cols": feature_cols,
            "patients_per_nurse": PATIENTS_PER_NURSE,
            "mae": mae,
            "r2": r2,
        },
        MODEL_PATH,
    )
    print("\nSUCCESS: Modelul a fost antrenat și salvat cu succes! ✅")


if __name__ == "__main__":
    train()
