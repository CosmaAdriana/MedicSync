"""
MedicSync — Patients Router
GET  /patients              — list patients (optional ?status= filter)
POST /patients              — register a new patient
GET  /patients/{id}         — patient details
GET  /patients/{id}/vitals  — vital signs history
GET  /patients/{id}/alerts  — clinical alerts
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import ClinicalAlert, Patient, PatientStatusEnum, RiskLevelEnum, User, VitalSign
from ..schemas import ClinicalAlertOut, PatientCreate, PatientOut, PatientStatusUpdate, VitalSignOut

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/hospital-stats")
def hospital_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models import Department
    rows = (
        db.query(
            Department.id.label("department_id"),
            Department.name.label("department_name"),
            func.count(Patient.id).label("total"),
            func.sum(case((Patient.status == PatientStatusEnum.admitted, 1), else_=0)).label("admitted"),
            func.sum(case((Patient.status == PatientStatusEnum.critical, 1), else_=0)).label("critical"),
            func.sum(case((Patient.status == PatientStatusEnum.discharged, 1), else_=0)).label("discharged"),
        )
        .outerjoin(Patient, Patient.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .all()
    )
    return [
        {
            "department_id": r.department_id,
            "department_name": r.department_name,
            "total": r.total or 0,
            "admitted": r.admitted or 0,
            "critical": r.critical or 0,
            "discharged": r.discharged or 0,
        }
        for r in rows
    ]


@router.get("/", response_model=list[PatientOut])
def list_patients(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Patient)
    if status:
        query = query.filter(Patient.status == status)
    if current_user.role.value in ("nurse", "doctor") and current_user.department_id:
        query = query.filter(Patient.department_id == current_user.department_id)
    return query.order_by(Patient.admission_date.desc()).all()


@router.post("/", response_model=PatientOut, status_code=201)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(
        full_name=patient_in.full_name,
        admission_date=patient_in.admission_date or date.today(),
        status=patient_in.status,
        department_id=patient_in.department_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    current_user: User = Depends(require_role("doctor", "nurse", "manager")),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.")
    return patient


@router.patch("/{patient_id}/status", response_model=PatientOut)
def update_patient_status(
    patient_id: int,
    body: PatientStatusUpdate,
    current_user: User = Depends(require_role("doctor", "manager")),
    db: Session = Depends(get_db),
):
    allowed = {"admitted", "discharged", "critical"}
    if body.status not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Status invalid. Valori acceptate: {', '.join(allowed)}")
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.")
    patient.status = body.status
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}/vitals", response_model=list[VitalSignOut])
def get_patient_vitals(
    patient_id: int,
    current_user: User = Depends(require_role("doctor", "nurse", "manager")),
    db: Session = Depends(get_db),
):
    if not db.query(Patient.id).filter(Patient.id == patient_id).scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.")
    return (
        db.query(VitalSign)
        .filter(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.recorded_at.desc())
        .all()
    )


@router.get("/{patient_id}/alerts", response_model=list[ClinicalAlertOut])
def get_patient_alerts(
    patient_id: int,
    current_user: User = Depends(require_role("doctor", "nurse", "manager")),
    db: Session = Depends(get_db),
):
    if not db.query(Patient.id).filter(Patient.id == patient_id).scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Pacientul cu ID {patient_id} nu a fost găsit.")
    return (
        db.query(ClinicalAlert)
        .filter(ClinicalAlert.patient_id == patient_id)
        .order_by(ClinicalAlert.created_at.desc())
        .all()
    )


@router.patch("/{patient_id}/alerts/{alert_id}/resolve", response_model=ClinicalAlertOut)
def resolve_alert(
    patient_id: int,
    alert_id: int,
    current_user: User = Depends(require_role("doctor", "nurse", "manager")),
    db: Session = Depends(get_db),
):
    alert = (
        db.query(ClinicalAlert)
        .filter(ClinicalAlert.id == alert_id, ClinicalAlert.patient_id == patient_id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Alerta cu ID {alert_id} nu a fost găsită.")

    alert.is_resolved = True
    db.commit()

    remaining = (
        db.query(ClinicalAlert)
        .filter(
            ClinicalAlert.patient_id == patient_id,
            ClinicalAlert.is_resolved == False,
            ClinicalAlert.risk_level == RiskLevelEnum.critical,
        )
        .count()
    )
    if remaining == 0:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient and patient.status == PatientStatusEnum.critical:
            patient.status = PatientStatusEnum.admitted
            db.commit()

    db.refresh(alert)
    return alert
