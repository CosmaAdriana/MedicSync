"""
MedicSync — FHIR Interoperability Router
Exposes existing data in HL7 FHIR R4-compatible JSON format.

GET /fhir/Patient              — Bundle of all patients as FHIR Patient resources
GET /fhir/Patient/{id}         — Single FHIR Patient resource
GET /fhir/Observation          — FHIR Observation (vital signs) for a patient
GET /fhir/Flag                 — FHIR Flag (clinical alerts) for a patient

These endpoints are READ-ONLY and serve as an interoperability layer.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..fhir_schemas import (
    FhirBundle,
    FhirBundleEntry,
    alert_to_fhir,
    patient_to_fhir,
    vital_to_fhir,
)
from ..models import ClinicalAlert, Patient, User, VitalSign

router = APIRouter(prefix="/fhir", tags=["FHIR (Interoperability)"])


# ---------------------------------------------------------------------------
# GET /fhir/Patient — Bundle of all patients
# ---------------------------------------------------------------------------
@router.get("/Patient", response_model=FhirBundle)
def list_fhir_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all patients as a FHIR **Bundle** of **Patient** resources.

    🔒 Requires: any authenticated user.
    """
    patients = db.query(Patient).order_by(Patient.id).all()

    entries = [
        FhirBundleEntry(resource=patient_to_fhir(p).model_dump())
        for p in patients
    ]

    return FhirBundle(
        type="searchset",
        total=len(entries),
        entry=entries,
    )


# ---------------------------------------------------------------------------
# GET /fhir/Patient/{id} — Single FHIR Patient
# ---------------------------------------------------------------------------
@router.get("/Patient/{patient_id}")
def get_fhir_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a single patient as a FHIR **Patient** resource.

    🔒 Requires: any authenticated user.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient/{patient_id} not found.",
        )
    return patient_to_fhir(patient)


# ---------------------------------------------------------------------------
# GET /fhir/Observation?patient={id} — Vital signs as FHIR Observations
# ---------------------------------------------------------------------------
@router.get("/Observation", response_model=FhirBundle)
def list_fhir_observations(
    patient: Optional[int] = Query(None, description="Filter by patient ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return vital signs as a FHIR **Bundle** of **Observation** resources.

    Use `?patient={id}` to filter by patient.

    🔒 Requires: any authenticated user.
    """
    query = db.query(VitalSign)
    if patient:
        query = query.filter(VitalSign.patient_id == patient)

    vitals = query.order_by(VitalSign.recorded_at.desc()).limit(100).all()

    entries = [
        FhirBundleEntry(resource=vital_to_fhir(v).model_dump())
        for v in vitals
    ]

    return FhirBundle(
        type="searchset",
        total=len(entries),
        entry=entries,
    )


# ---------------------------------------------------------------------------
# GET /fhir/Flag?patient={id} — Clinical alerts as FHIR Flags
# ---------------------------------------------------------------------------
@router.get("/Flag", response_model=FhirBundle)
def list_fhir_flags(
    patient: Optional[int] = Query(None, description="Filter by patient ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return clinical alerts as a FHIR **Bundle** of **Flag** resources.

    Use `?patient={id}` to filter by patient.

    🔒 Requires: any authenticated user.
    """
    query = db.query(ClinicalAlert)
    if patient:
        query = query.filter(ClinicalAlert.patient_id == patient)

    alerts = query.order_by(ClinicalAlert.created_at.desc()).limit(100).all()

    entries = [
        FhirBundleEntry(resource=alert_to_fhir(a).model_dump())
        for a in alerts
    ]

    return FhirBundle(
        type="searchset",
        total=len(entries),
        entry=entries,
    )
