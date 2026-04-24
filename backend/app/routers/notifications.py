"""
MedicSync — Notifications Router
GET /notifications/summary — counts for sidebar badges, scoped by role.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    ClinicalAlert, Order, OrderStatusEnum, Patient,
    RiskLevelEnum, VacationRequest, VacationRequestStatusEnum, User,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/summary")
def notifications_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returnează contoare pentru badge-urile din sidebar.
    - critical_alerts:          alerte critice nerezolvate (dept. propriu pt. nurse/doctor, global pt. manager)
    - pending_orders:           comenzi cu status 'placed' (manager + inventory_manager)
    - pending_vacation_requests: cereri concediu în așteptare (doar manager)
    """
    role = current_user.role.value

    # Toate alertele nerezolvate
    alerts_q = (
        db.query(func.count(ClinicalAlert.id))
        .join(Patient, ClinicalAlert.patient_id == Patient.id)
        .filter(ClinicalAlert.is_resolved == False)
    )
    if role in ("nurse", "doctor") and current_user.department_id:
        alerts_q = alerts_q.filter(Patient.department_id == current_user.department_id)

    critical_alerts = alerts_q.scalar() or 0

    # Comenzi în așteptare de aprobare (status placed)
    pending_orders = 0
    if role in ("manager", "inventory_manager"):
        pending_orders = (
            db.query(func.count(Order.id))
            .filter(Order.status == OrderStatusEnum.placed)
            .scalar()
        ) or 0

    # Cereri concediu neaprobate (doar manager)
    pending_vacation = 0
    if role == "manager":
        pending_vacation = (
            db.query(func.count(VacationRequest.id))
            .filter(VacationRequest.status == VacationRequestStatusEnum.pending)
            .scalar()
        ) or 0

    return {
        "critical_alerts": critical_alerts,
        "pending_orders": pending_orders,
        "pending_vacation_requests": pending_vacation,
    }
