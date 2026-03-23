"""
MedicSync — Predictions Router (Health 4.0)
GET /predict/staff-needs  — ML-powered staff requirement prediction
GET /predict/inventory    — Safety stock calculation 
"""

import math
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import InventoryItem, User
from ..schemas import InventoryPredictionItemOut, StaffPredictionOut
from ..services.staff_predictor import predict_staff_needs

router = APIRouter(prefix="/predict", tags=["Predictions (AI/ML)"])


# ---------------------------------------------------------------------------
# GET /predict/staff-needs
# ---------------------------------------------------------------------------
@router.get("/staff-needs", response_model=StaffPredictionOut)
def get_staff_prediction(
    target_date: date = Query(..., alias="date", description="Data pentru predicție (YYYY-MM-DD)"),
    weather_temp: float = Query(..., description="Temperatura estimată (°C)"),
    is_holiday: bool = Query(False, description="Este zi de sărbătoare?"),
    is_epidemic: bool = Query(False, description="Este perioadă de epidemie?"),
    current_user: User = Depends(require_role("manager")),
):
    """
    Predict the number of patients and recommended nursing staff for a given day.

    Uses a RandomForest model trained on 3 years of historical admission data,
    taking into account seasonality, weather, holidays, and epidemic periods.

    🔒 Requires: **manager** role.
    """
    try:
        result = predict_staff_needs(target_date, weather_temp, is_holiday, is_epidemic)
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# GET /predict/inventory — Safety Stock (SS = Z * σ_L * √D_avg)
# ---------------------------------------------------------------------------
# Z = 1.65  (95% service level)
# σ_L = lead time std dev in days (configurable, default 2)
# D_avg = average daily consumption (estimated from min_stock_level as proxy)
Z_SCORE = 1.65
DEFAULT_LEAD_TIME_STD = 2.0  # days


@router.get("/inventory", response_model=list[InventoryPredictionItemOut])
def get_inventory_prediction(
    lead_time_std: float = Query(DEFAULT_LEAD_TIME_STD, description="Deviația standard a timpului de livrare (zile)"),
    current_user: User = Depends(require_role("inventory_manager")),
    db: Session = Depends(get_db),
):
    """
    Calculate the safety stock for each inventory item using the formula:

        **SS = Z · σ_L · √D_avg**

    Where:
    - Z = 1.65 (95% service level)
    - σ_L = standard deviation of lead time (configurable)
    - D_avg = estimated average daily consumption

    Also indicates whether a reorder is needed (current_stock < safety_stock + min_stock_level).

    🔒 Requires: **inventory_manager** role.
    """
    items = db.query(InventoryItem).order_by(InventoryItem.product_name).all()
    results = []

    for item in items:
        # Estimate avg daily consumption from min_stock_level
        # (min_stock_level represents roughly a week's worth of supply)
        avg_daily = item.min_stock_level / 7.0 if item.min_stock_level > 0 else 1.0

        safety_stock = math.ceil(Z_SCORE * lead_time_std * math.sqrt(avg_daily))

        reorder_needed = item.current_stock < (safety_stock + item.min_stock_level)

        results.append(
            InventoryPredictionItemOut(
                product_name=item.product_name,
                current_stock=item.current_stock,
                min_stock_level=item.min_stock_level,
                avg_daily_consumption=round(avg_daily, 2),
                safety_stock=safety_stock,
                reorder_needed=reorder_needed,
            )
        )

    return results
