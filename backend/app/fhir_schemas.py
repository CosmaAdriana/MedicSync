"""
MedicSync — FHIR-Compatible Schemas & Mappers
Pydantic models that mirror HL7 FHIR resource structures (R4)
and helper functions to convert MedicSync ORM objects into FHIR JSON.

This is a SIMULATION layer for interoperability readiness,
not a full FHIR server implementation.
"""

from datetime import datetime, date
from typing import Any, Optional

from pydantic import BaseModel

from .models import ClinicalAlert, InventoryItem, Patient, VitalSign


# ========================== FHIR Building Blocks ===========================

class FhirMeta(BaseModel):
    """FHIR Resource metadata."""
    versionId: str = "1"
    lastUpdated: str


class FhirIdentifier(BaseModel):
    """FHIR Identifier — links to internal MedicSync IDs."""
    system: str = "https://medicsync.local/id"
    value: str


class FhirCoding(BaseModel):
    """FHIR Coding — a code from a code system."""
    system: str
    code: str
    display: str


class FhirCodeableConcept(BaseModel):
    """FHIR CodeableConcept — a concept with one or more codings."""
    coding: list[FhirCoding]
    text: Optional[str] = None


class FhirReference(BaseModel):
    """FHIR Reference — a pointer to another resource."""
    reference: str
    display: Optional[str] = None


class FhirQuantity(BaseModel):
    """FHIR Quantity — a measured value with unit."""
    value: float
    unit: str
    system: str = "http://unitsofmeasure.org"
    code: str


class FhirComponent(BaseModel):
    """FHIR Observation component — for multi-value observations."""
    code: FhirCodeableConcept
    valueQuantity: Optional[FhirQuantity] = None
    valueString: Optional[str] = None


class FhirBundleEntry(BaseModel):
    """Single entry in a FHIR Bundle."""
    resource: dict[str, Any]


class FhirBundle(BaseModel):
    """FHIR Bundle — collection of resources."""
    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int
    entry: list[FhirBundleEntry]


# ========================== FHIR Resources =================================

class FhirPatient(BaseModel):
    """HL7 FHIR Patient Resource (simplified)."""
    resourceType: str = "Patient"
    id: str
    meta: FhirMeta
    identifier: list[FhirIdentifier]
    name: list[dict[str, Any]]
    active: bool
    status: Optional[str] = None


class FhirObservation(BaseModel):
    """HL7 FHIR Observation Resource — maps VitalSign."""
    resourceType: str = "Observation"
    id: str
    meta: FhirMeta
    identifier: list[FhirIdentifier]
    status: str = "final"
    category: list[FhirCodeableConcept]
    code: FhirCodeableConcept
    subject: FhirReference
    effectiveDateTime: str
    component: list[FhirComponent]


class FhirFlag(BaseModel):
    """HL7 FHIR Flag Resource — maps ClinicalAlert."""
    resourceType: str = "Flag"
    id: str
    meta: FhirMeta
    identifier: list[FhirIdentifier]
    status: str
    category: list[FhirCodeableConcept]
    code: FhirCodeableConcept
    subject: FhirReference
    period: dict[str, str]


# ========================== Mapping Functions ==============================

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _split_name(full_name: str) -> dict:
    """Split a full name into FHIR HumanName structure."""
    parts = full_name.strip().split()
    family = parts[-1] if parts else ""
    given = parts[:-1] if len(parts) > 1 else []
    return {"use": "official", "family": family, "given": given, "text": full_name}


def patient_to_fhir(patient: Patient) -> FhirPatient:
    """Convert a MedicSync Patient ORM object to a FHIR Patient resource."""
    admission_str = (
        patient.admission_date.isoformat()
        if isinstance(patient.admission_date, (date, datetime))
        else str(patient.admission_date)
    )

    return FhirPatient(
        id=str(patient.id),
        meta=FhirMeta(lastUpdated=admission_str + "T00:00:00Z"),
        identifier=[
            FhirIdentifier(
                system="https://medicsync.local/patients",
                value=str(patient.id),
            )
        ],
        name=[_split_name(patient.full_name)],
        active=patient.status.value != "discharged" if hasattr(patient.status, 'value') else patient.status != "discharged",
        status=patient.status.value if hasattr(patient.status, 'value') else patient.status,
    )


def vital_to_fhir(vital: VitalSign) -> FhirObservation:
    """Convert a MedicSync VitalSign ORM object to a FHIR Observation resource."""
    recorded = (
        vital.recorded_at.isoformat() + "Z"
        if vital.recorded_at
        else _now_iso()
    )

    # Parse blood pressure
    bp_parts = vital.blood_pressure.split("/")
    systolic = int(bp_parts[0]) if len(bp_parts) >= 1 else 0
    diastolic = int(bp_parts[1]) if len(bp_parts) >= 2 else 0

    return FhirObservation(
        id=str(vital.id),
        meta=FhirMeta(lastUpdated=recorded),
        identifier=[
            FhirIdentifier(
                system="https://medicsync.local/vitals",
                value=str(vital.id),
            )
        ],
        status="final",
        category=[
            FhirCodeableConcept(
                coding=[FhirCoding(
                    system="http://terminology.hl7.org/CodeSystem/observation-category",
                    code="vital-signs",
                    display="Vital Signs",
                )],
                text="Vital Signs",
            )
        ],
        code=FhirCodeableConcept(
            coding=[FhirCoding(
                system="http://loinc.org",
                code="85353-1",
                display="Vital signs, weight, height, head circumference, oxygen saturation and BMI panel",
            )],
            text="Vital Signs Panel",
        ),
        subject=FhirReference(
            reference=f"Patient/{vital.patient_id}",
        ),
        effectiveDateTime=recorded,
        component=[
            FhirComponent(
                code=FhirCodeableConcept(
                    coding=[FhirCoding(system="http://loinc.org", code="8480-6", display="Systolic blood pressure")],
                ),
                valueQuantity=FhirQuantity(value=float(systolic), unit="mmHg", code="mm[Hg]"),
            ),
            FhirComponent(
                code=FhirCodeableConcept(
                    coding=[FhirCoding(system="http://loinc.org", code="8462-4", display="Diastolic blood pressure")],
                ),
                valueQuantity=FhirQuantity(value=float(diastolic), unit="mmHg", code="mm[Hg]"),
            ),
            FhirComponent(
                code=FhirCodeableConcept(
                    coding=[FhirCoding(system="http://loinc.org", code="8867-4", display="Heart rate")],
                ),
                valueQuantity=FhirQuantity(value=float(vital.pulse), unit="beats/minute", code="/min"),
            ),
            FhirComponent(
                code=FhirCodeableConcept(
                    coding=[FhirCoding(system="http://loinc.org", code="9279-1", display="Respiratory rate")],
                ),
                valueQuantity=FhirQuantity(value=float(vital.respiratory_rate), unit="breaths/minute", code="/min"),
            ),
            FhirComponent(
                code=FhirCodeableConcept(
                    coding=[FhirCoding(system="http://loinc.org", code="2708-6", display="Oxygen saturation")],
                ),
                valueQuantity=FhirQuantity(value=vital.oxygen_saturation, unit="%", code="%"),
            ),
        ],
    )


def alert_to_fhir(alert: ClinicalAlert) -> FhirFlag:
    """Convert a MedicSync ClinicalAlert ORM object to a FHIR Flag resource."""
    risk = alert.risk_level.value if hasattr(alert.risk_level, 'value') else alert.risk_level
    created = (
        alert.created_at.isoformat() + "Z"
        if alert.created_at
        else _now_iso()
    )

    # Map MedicSync risk level to FHIR Flag status
    fhir_status = "inactive" if alert.is_resolved else "active"

    return FhirFlag(
        id=str(alert.id),
        meta=FhirMeta(lastUpdated=created),
        identifier=[
            FhirIdentifier(
                system="https://medicsync.local/alerts",
                value=str(alert.id),
            )
        ],
        status=fhir_status,
        category=[
            FhirCodeableConcept(
                coding=[FhirCoding(
                    system="http://terminology.hl7.org/CodeSystem/flag-category",
                    code="clinical",
                    display="Clinical",
                )],
                text="Clinical Alert",
            )
        ],
        code=FhirCodeableConcept(
            coding=[FhirCoding(
                system="https://medicsync.local/risk-level",
                code=risk,
                display=f"Risk Level: {risk.capitalize()}",
            )],
            text=alert.message,
        ),
        subject=FhirReference(
            reference=f"Patient/{alert.patient_id}",
        ),
        period={"start": created},
    )
