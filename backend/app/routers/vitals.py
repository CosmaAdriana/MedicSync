"""
MedicSync — Vitals Router
POST /vitals — record vital signs at the patient's bedside (cap. 1.2.2).
Only nurses (role = "nurse") are allowed to record vital signs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import Patient, User, VitalSign
from ..schemas import VitalSignCreate, VitalSignOut

router = APIRouter(prefix="/vitals", tags=["Vital Signs"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/", response_model=VitalSignOut, status_code=201)
def record_vitals(
    vitals_in: VitalSignCreate,
    current_user: User = Depends(require_role("nurse")),
    db: Session = Depends(get_db),
):
    """
    Record a new set of vital signs for an admitted patient.

    🔒 Requires: **nurse** role (JWT Bearer token).
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == vitals_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pacientul cu ID {vitals_in.patient_id} nu a fost găsit.",
        )

    vital_sign = VitalSign(
        patient_id=vitals_in.patient_id,
        blood_pressure=vitals_in.blood_pressure,
        pulse=vitals_in.pulse,
        respiratory_rate=vitals_in.respiratory_rate,
        oxygen_saturation=vitals_in.oxygen_saturation,
    )
    db.add(vital_sign)
    db.commit()
    db.refresh(vital_sign)
    return vital_sign
