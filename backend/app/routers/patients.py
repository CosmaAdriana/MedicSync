"""
MedicSync — Patients Router
GET  /patients              — list patients (optional ?status= filter).
POST /patients              — register a new patient.
GET  /patients/{id}         — patient details.
GET  /patients/{id}/vitals  — vital signs history for a patient.
GET  /patients/{id}/alerts  — clinical alerts for a patient.

🔒 Detail/vitals/alerts endpoints require: doctor or nurse role.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import ClinicalAlert, Patient, User, VitalSign
from ..schemas import ClinicalAlertOut, PatientCreate, PatientOut, VitalSignOut

router = APIRouter(prefix="/patients", tags=["Patients"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[PatientOut])
def list_patients(
    status: Optional[str] = Query(None, description="Filter by status: admitted | discharged | critical"),
    db: Session = Depends(get_db),
):
    """
    Return all patients, optionally filtered by status.
    """
    query = db.query(Patient)

    if status:
        query = query.filter(Patient.status == status)

    return query.order_by(Patient.admission_date.desc()).all()


@router.post("/", response_model=PatientOut, status_code=201)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    """
    Register a new patient in the system.
    """
    patient = Patient(
        full_name=patient_in.full_name,
        admission_date=patient_in.admission_date or date.today(),
        status=patient_in.status,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    current_user: User = Depends(require_role("doctor", "nurse")),
    db: Session = Depends(get_db),
):
    """
    Return details for a single patient.

    🔒 Requires: **doctor** or **nurse** role.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.",
        )
    return patient


@router.get("/{patient_id}/vitals", response_model=list[VitalSignOut])
def get_patient_vitals(
    patient_id: int,
    current_user: User = Depends(require_role("doctor", "nurse")),
    db: Session = Depends(get_db),
):
    """
    Return the vital signs history for a patient (newest first).

    🔒 Requires: **doctor** or **nurse** role.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.",
        )
    return (
        db.query(VitalSign)
        .filter(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.recorded_at.desc())
        .all()
    )


@router.get("/{patient_id}/alerts", response_model=list[ClinicalAlertOut])
def get_patient_alerts(
    patient_id: int,
    current_user: User = Depends(require_role("doctor", "nurse")),
    db: Session = Depends(get_db),
):
    """
    Return clinical alerts for a patient (newest first).

    🔒 Requires: **doctor** or **nurse** role.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.",
        )
    return (
        db.query(ClinicalAlert)
        .filter(ClinicalAlert.patient_id == patient_id)
        .order_by(ClinicalAlert.created_at.desc())
        .all()
    )
