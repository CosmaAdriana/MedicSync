"""
MedicSync — Predictions Router
GET /predict/model-info   — real metrics and feature importances from ML bundle
GET /predict/staff-needs  — ML-powered staff requirement prediction
GET /predict/inventory    — safety stock calculation (SS = Z · σ_L · √D_avg)
"""

import math
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import Department, InventoryItem, User
from ..schemas import InventoryPredictionItemOut, StaffPredictionOut
from ..services.staff_predictor import predict_staff_needs, _load_model

router = APIRouter(prefix="/predict", tags=["Predictions (AI/ML)"])


@router.get("/model-info")
def get_model_info(
    current_user: User = Depends(require_role("manager")),
):
    try:
        bundle = _load_model()
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    importances = {
        col: round(float(imp), 4)
        for col, imp in zip(feature_cols, model.feature_importances_)
    }
    return {
        "r2": round(float(bundle["r2"]), 4),
        "mae": round(float(bundle["mae"]), 2),
        "n_estimators": model.n_estimators,
        "max_depth": model.max_depth,
        "patients_per_nurse": bundle["patients_per_nurse"],
        "feature_importances": dict(sorted(importances.items(), key=lambda x: -x[1])),
    }


@router.get("/staff-needs", response_model=StaffPredictionOut)
def get_staff_prediction(
    target_date: date = Query(..., alias="date"),
    weather_temp: float = Query(...),
    department_id: int = Query(...),
    is_holiday: bool = Query(False),
    is_epidemic: bool = Query(False),
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Departamentul cu ID {department_id} nu există.")
    try:
        return predict_staff_needs(target_date, weather_temp, is_holiday, is_epidemic,
                                   department_id, department.name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


Z_SCORE = 1.65
DEFAULT_LEAD_TIME_STD = 2.0


@router.get("/inventory", response_model=list[InventoryPredictionItemOut])
def get_inventory_prediction(
    lead_time_std: float = Query(DEFAULT_LEAD_TIME_STD),
    current_user: User = Depends(require_role("inventory_manager")),
    db: Session = Depends(get_db),
):
    items = db.query(InventoryItem).order_by(InventoryItem.product_name).all()
    results = []
    for item in items:
        avg_daily = item.min_stock_level / 7.0 if item.min_stock_level > 0 else 1.0
        safety_stock = math.ceil(Z_SCORE * lead_time_std * math.sqrt(avg_daily))
        results.append(InventoryPredictionItemOut(
            product_name=item.product_name,
            current_stock=item.current_stock,
            min_stock_level=item.min_stock_level,
            avg_daily_consumption=round(avg_daily, 2),
            safety_stock=safety_stock,
            reorder_needed=item.current_stock < (safety_stock + item.min_stock_level),
        ))
    return results
