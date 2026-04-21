"""
MedicSync — Clinical Analyzer Service
Analyzes vital signs against clinical thresholds and generates
ClinicalAlert records when risk is detected.
"""

from typing import Optional

from sqlalchemy.orm import Session

from ..models import ClinicalAlert, RiskLevelEnum, VitalSign


def _parse_systolic(bp_str: str) -> int:
    try:
        return int(bp_str.split("/")[0])
    except (ValueError, IndexError):
        return 120


def analyze_vitals(vital: VitalSign, db: Session) -> Optional[ClinicalAlert]:
    systolic = _parse_systolic(vital.blood_pressure)
    findings = []

    if vital.oxygen_saturation < 92:
        findings.append((RiskLevelEnum.critical, f"Hipoxie severă: SpO₂ = {vital.oxygen_saturation}%"))
    if vital.pulse > 150:
        findings.append((RiskLevelEnum.critical, f"Tahicardie severă: Puls = {vital.pulse} bpm"))
    if vital.pulse < 40:
        findings.append((RiskLevelEnum.critical, f"Bradicardie severă: Puls = {vital.pulse} bpm"))

    if vital.pulse > 130 and vital.pulse <= 150:
        findings.append((RiskLevelEnum.high, f"Tahicardie: Puls = {vital.pulse} bpm"))
    if vital.pulse < 50 and vital.pulse >= 40:
        findings.append((RiskLevelEnum.high, f"Bradicardie: Puls = {vital.pulse} bpm"))
    if vital.respiratory_rate > 28:
        findings.append((RiskLevelEnum.high, f"Tahipnee: FR = {vital.respiratory_rate} resp/min"))
    if vital.respiratory_rate < 10:
        findings.append((RiskLevelEnum.high, f"Bradipnee: FR = {vital.respiratory_rate} resp/min"))
    if systolic > 180:
        findings.append((RiskLevelEnum.high, f"Criză hipertensivă: TA = {vital.blood_pressure} mmHg"))
    if systolic < 90:
        findings.append((RiskLevelEnum.high, f"Hipotensiune: TA = {vital.blood_pressure} mmHg"))

    if vital.oxygen_saturation < 95 and vital.oxygen_saturation >= 92:
        findings.append((RiskLevelEnum.medium, f"SpO₂ scăzut: {vital.oxygen_saturation}%"))
    if vital.pulse > 110 and vital.pulse <= 130:
        findings.append((RiskLevelEnum.medium, f"Puls crescut: {vital.pulse} bpm"))
    if vital.respiratory_rate > 22 and vital.respiratory_rate <= 28:
        findings.append((RiskLevelEnum.medium, f"Frecvență respiratorie crescută: {vital.respiratory_rate} resp/min"))

    if not findings:
        return None

    severity_order = {
        RiskLevelEnum.critical: 4,
        RiskLevelEnum.high: 3,
        RiskLevelEnum.medium: 2,
        RiskLevelEnum.low: 1,
    }
    findings.sort(key=lambda f: severity_order[f[0]], reverse=True)
    worst_level = findings[0][0]
    message = " | ".join(f"[{f[0].value.upper()}] {f[1]}" for f in findings)

    alert = ClinicalAlert(
        patient_id=vital.patient_id,
        risk_level=worst_level,
        message=message,
        is_resolved=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
