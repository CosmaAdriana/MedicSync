"""
MedicSync — Staff Prediction Service
Loads the trained RandomForest model and predicts patient count and nurse needs
for a given date, department and exogenous variables.
"""

import math
import os
from datetime import date

import joblib

MODEL_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "ml_engine", "staff_model.joblib",
))

_model_cache = None


def _load_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Modelul ML nu a fost găsit la '{MODEL_PATH}'. "
            "Rulează mai întâi: python ml_engine/train_staff_model.py"
        )
    _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def predict_staff_needs(
    target_date: date,
    weather_temp: float,
    is_holiday: bool,
    is_epidemic: bool,
    department_id: int,
    department_name: str = None,
) -> dict:
    bundle = _load_model()
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    patients_per_nurse = bundle["patients_per_nurse"]

    import pandas as pd

    features = pd.DataFrame(
        [{
            "month": target_date.month,
            "day_of_week": target_date.weekday(),
            "weather_temp": weather_temp,
            "is_holiday": int(is_holiday),
            "is_epidemic": int(is_epidemic),
            "department_id": department_id,
        }],
        columns=feature_cols,
    )

    predicted_patients = max(1, round(float(model.predict(features)[0])))
    recommended_nurses = math.ceil(predicted_patients / patients_per_nurse)

    result = {
        "date": target_date.isoformat(),
        "predicted_patients": predicted_patients,
        "recommended_nurses": recommended_nurses,
        "model_r2": round(bundle["r2"], 4),
        "model_mae": round(bundle["mae"], 2),
    }
    if department_name:
        result["department_name"] = department_name

    return result
