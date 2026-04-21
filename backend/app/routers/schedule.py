"""
MedicSync — Schedule Router (Grafic Lunar)

Endpoints:
  GET  /schedule/balance                   — sold concediu utilizator curent
  GET  /schedule/requests                  — lista cereri (proprii / toate per dept)
  POST /schedule/requests                  — depune cerere (nurse)
  PATCH /schedule/requests/{id}            — aprobă/respinge cerere (manager)
  POST /schedule/generate                  — generează grafic AI (manager)
  GET  /schedule/monthly                   — grafic salvat
  POST /schedule/save                      — salvează grafic (manager)
"""

import calendar
import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import (
    User, VacationRequest, VacationRequestStatusEnum, RequestTypeEnum,
    VacationBalance, MonthlySchedule,
)
from ..schemas import (
    VacationRequestCreate, VacationRequestOut, VacationRequestStatusUpdate,
    VacationBalanceOut, ScheduleGenerateRequest, MonthlyScheduleOut, ScheduleSaveRequest,
)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


# ---------------------------------------------------------------------------
# Helper: sold concediu (auto-create dacă nu există)
# ---------------------------------------------------------------------------
def _get_or_create_balance(db: Session, user_id: int, year: int) -> VacationBalance:
    balance = (
        db.query(VacationBalance)
        .filter(VacationBalance.user_id == user_id, VacationBalance.year == year)
        .first()
    )
    if not balance:
        balance = VacationBalance(user_id=user_id, year=year, total_days=21, used_days=0)
        db.add(balance)
        db.commit()
        db.refresh(balance)
    return balance


def _count_days(start: date, end: date) -> int:
    return (end - start).days + 1


# ---------------------------------------------------------------------------
# Sold concediu
# ---------------------------------------------------------------------------
@router.get("/balance", response_model=VacationBalanceOut)
def get_balance(
    year: int = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează soldul de zile de concediu al utilizatorului curent."""
    if year is None:
        year = date.today().year
    balance = _get_or_create_balance(db, current_user.id, year)
    return VacationBalanceOut(
        user_id=balance.user_id,
        year=balance.year,
        total_days=balance.total_days,
        used_days=balance.used_days,
        remaining_days=balance.total_days - balance.used_days,
    )


# ---------------------------------------------------------------------------
# Cereri concediu / zi liberă
# ---------------------------------------------------------------------------
@router.get("/requests", response_model=list[VacationRequestOut])
def list_requests(
    department_id: int = Query(default=None),
    month: int = Query(default=None),
    year: int = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Asistent: vede doar propriile cereri.
    Manager: vede cererile asistenților din departamentul selectat.
    """
    from ..models import RoleEnum

    q = db.query(VacationRequest)

    if current_user.role.value == "nurse":
        q = q.filter(VacationRequest.nurse_id == current_user.id)
    elif current_user.role.value == "manager":
        # Folosește department_id din query param; fallback la departamentul managerului
        target_dept = department_id or current_user.department_id
        dept_nurses = (
            db.query(User.id)
            .filter(
                User.department_id == target_dept,
                User.role == RoleEnum.nurse,
            )
            .subquery()
        )
        q = q.filter(VacationRequest.nurse_id.in_(dept_nurses))
    else:
        raise HTTPException(status_code=403, detail="Acces interzis.")

    if year:
        q = q.filter(
            VacationRequest.start_date >= date(year, 1, 1),
            VacationRequest.end_date <= date(year, 12, 31),
        )

    requests = q.order_by(VacationRequest.created_at.desc()).all()

    result = []
    for r in requests:
        out = VacationRequestOut(
            id=r.id,
            nurse_id=r.nurse_id,
            nurse_name=r.nurse.full_name if r.nurse else None,
            request_type=r.request_type.value,
            start_date=r.start_date,
            end_date=r.end_date,
            status=r.status.value,
            notes=r.notes,
            created_at=r.created_at,
        )
        result.append(out)
    return result


@router.post("/requests", response_model=VacationRequestOut, status_code=201)
def create_request(
    req_in: VacationRequestCreate,
    current_user: User = Depends(require_role("nurse")),
    db: Session = Depends(get_db),
):
    """Asistentul depune o cerere de concediu sau zi liberă."""
    if req_in.end_date < req_in.start_date:
        raise HTTPException(status_code=422, detail="Data de sfârșit trebuie să fie după data de început.")

    days_requested = _count_days(req_in.start_date, req_in.end_date)

    # Verificare sold pentru concediu
    if req_in.request_type == "vacation":
        balance = _get_or_create_balance(db, current_user.id, req_in.start_date.year)
        remaining = balance.total_days - balance.used_days
        if days_requested > remaining:
            raise HTTPException(
                status_code=422,
                detail=f"Sold insuficient: {remaining} zile disponibile, ai solicitat {days_requested}.",
            )

    # Verificare suprapunere cu cereri existente
    overlap = (
        db.query(VacationRequest)
        .filter(
            VacationRequest.nurse_id == current_user.id,
            VacationRequest.status != VacationRequestStatusEnum.rejected,
            VacationRequest.start_date <= req_in.end_date,
            VacationRequest.end_date >= req_in.start_date,
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=f"Există deja o cerere pentru această perioadă ({overlap.start_date} – {overlap.end_date}).",
        )

    req = VacationRequest(
        nurse_id=current_user.id,
        request_type=RequestTypeEnum(req_in.request_type),
        start_date=req_in.start_date,
        end_date=req_in.end_date,
        notes=req_in.notes,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    return VacationRequestOut(
        id=req.id,
        nurse_id=req.nurse_id,
        nurse_name=current_user.full_name,
        request_type=req.request_type.value,
        start_date=req.start_date,
        end_date=req.end_date,
        status=req.status.value,
        notes=req.notes,
        created_at=req.created_at,
    )


@router.patch("/requests/{request_id}", response_model=VacationRequestOut)
def review_request(
    request_id: int,
    update: VacationRequestStatusUpdate,
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    """Managerul aprobă sau respinge o cerere."""
    req = db.query(VacationRequest).filter(VacationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Cererea nu a fost găsită.")

    if update.status not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="Status invalid. Folosește 'approved' sau 'rejected'.")

    old_status = req.status
    new_status = VacationRequestStatusEnum(update.status)

    # La aprobare concediu → scade din sold
    if new_status == VacationRequestStatusEnum.approved and old_status != new_status:
        if req.request_type == RequestTypeEnum.vacation:
            balance = _get_or_create_balance(db, req.nurse_id, req.start_date.year)
            days = _count_days(req.start_date, req.end_date)
            balance.used_days = min(balance.used_days + days, balance.total_days)

    # La respingere după ce fusese aprobat → restituie zilele
    if new_status == VacationRequestStatusEnum.rejected and old_status == VacationRequestStatusEnum.approved:
        if req.request_type == RequestTypeEnum.vacation:
            balance = _get_or_create_balance(db, req.nurse_id, req.start_date.year)
            days = _count_days(req.start_date, req.end_date)
            balance.used_days = max(0, balance.used_days - days)

    req.status = new_status
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    return VacationRequestOut(
        id=req.id,
        nurse_id=req.nurse_id,
        nurse_name=req.nurse.full_name if req.nurse else None,
        request_type=req.request_type.value,
        start_date=req.start_date,
        end_date=req.end_date,
        status=req.status.value,
        notes=req.notes,
        created_at=req.created_at,
    )


# ---------------------------------------------------------------------------
# Generare grafic AI
# ---------------------------------------------------------------------------
@router.post("/generate")
def generate_schedule(
    req: ScheduleGenerateRequest,
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    """Generează graficul lunar optim cu AI (bazat pe predicții ML)."""
    from ..services.schedule_generator import generate_monthly_schedule

    if not (1 <= req.month <= 12):
        raise HTTPException(status_code=422, detail="Luna trebuie să fie între 1 și 12.")

    result = generate_monthly_schedule(db, req.department_id, req.year, req.month)
    return result


# ---------------------------------------------------------------------------
# Grafic salvat
# ---------------------------------------------------------------------------
@router.get("/monthly", response_model=MonthlyScheduleOut)
def get_monthly_schedule(
    department_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returnează graficul salvat pentru o lună și departament."""
    sched = (
        db.query(MonthlySchedule)
        .filter(
            MonthlySchedule.department_id == department_id,
            MonthlySchedule.year == year,
            MonthlySchedule.month == month,
        )
        .order_by(MonthlySchedule.created_at.desc())
        .first()
    )
    if not sched:
        raise HTTPException(status_code=404, detail="Nu există grafic salvat pentru această lună.")
    return sched


@router.post("/save", response_model=MonthlyScheduleOut, status_code=201)
def save_schedule(
    req: ScheduleSaveRequest,
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    """Salvează (sau suprascrie) graficul lunar."""
    # Verifică JSON valid
    try:
        json.loads(req.schedule_data)
    except ValueError:
        raise HTTPException(status_code=422, detail="schedule_data nu este JSON valid.")

    existing = (
        db.query(MonthlySchedule)
        .filter(
            MonthlySchedule.department_id == req.department_id,
            MonthlySchedule.year == req.year,
            MonthlySchedule.month == req.month,
        )
        .first()
    )

    if existing:
        existing.schedule_data = req.schedule_data
        existing.is_finalized = req.is_finalized
        existing.created_by = current_user.id
        existing.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    sched = MonthlySchedule(
        department_id=req.department_id,
        year=req.year,
        month=req.month,
        schedule_data=req.schedule_data,
        created_by=current_user.id,
        is_finalized=req.is_finalized,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched
