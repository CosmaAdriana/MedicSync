"""
MedicSync — Vitals Router
POST /vitals — record vital signs at the patient's bedside.
Only nurses (role = "nurse") are allowed to record vital signs.

After recording, vitals are automatically analyzed
for clinical risk. If a threshold is breached, a ClinicalAlert is generated.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import Patient, User, VitalSign
from ..schemas import VitalSignCreate, VitalSignOutWithAlert
from ..services.clinical_analyzer import analyze_vitals

router = APIRouter(prefix="/vitals", tags=["Vital Signs"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/", response_model=VitalSignOutWithAlert, status_code=201)
def record_vitals(
    vitals_in: VitalSignCreate,
    current_user: User = Depends(require_role("nurse")),
    db: Session = Depends(get_db),
):
    """
    Record a new set of vital signs for an admitted patient.
    **Automatically analyzes** the values and generates a ClinicalAlert
    if any clinical threshold is breached.

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

    #Clinical analysis
    alert = analyze_vitals(vital_sign, db)

    # Build response with optional alert
    response = {
        "id": vital_sign.id,
        "patient_id": vital_sign.patient_id,
        "blood_pressure": vital_sign.blood_pressure,
        "pulse": vital_sign.pulse,
        "respiratory_rate": vital_sign.respiratory_rate,
        "oxygen_saturation": vital_sign.oxygen_saturation,
        "recorded_at": vital_sign.recorded_at,
        "alert": None,
    }

    if alert:
        response["alert"] = {
            "id": alert.id,
            "patient_id": alert.patient_id,
            "risk_level": alert.risk_level.value,
            "message": alert.message,
            "is_resolved": alert.is_resolved,
            "created_at": alert.created_at,
        }

    return response
