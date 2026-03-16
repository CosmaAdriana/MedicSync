"""
MedicSync — Shifts Router
GET  /shifts  — list all work shifts.
POST /shifts  — assign a new shift to a staff member.

🔒 All endpoints require: manager role.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import Shift, User
from ..schemas import ShiftCreate, ShiftOut

router = APIRouter(prefix="/shifts", tags=["Shifts"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[ShiftOut])
def list_shifts(
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    """
    Return all shifts ordered by start time (newest first).

    🔒 Requires: **manager** role.
    """
    return db.query(Shift).order_by(Shift.start_time.desc()).all()


@router.post("/", response_model=ShiftOut, status_code=201)
def create_shift(
    shift_in: ShiftCreate,
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    """
    Assign a new work shift to a staff member.

    🔒 Requires: **manager** role.
    """
    # Verify the target user exists
    target_user = db.query(User).filter(User.id == shift_in.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilizatorul cu ID {shift_in.user_id} nu a fost găsit.",
        )

    if shift_in.end_time <= shift_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ora de sfârșit trebuie să fie după ora de început.",
        )

    shift = Shift(
        user_id=shift_in.user_id,
        start_time=shift_in.start_time,
        end_time=shift_in.end_time,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift
