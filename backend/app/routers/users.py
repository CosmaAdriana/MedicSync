"""
MedicSync — Users Router
Manager-only endpoints pentru gestionarea conturilor de personal.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import User, RoleEnum
from ..routers.auth import hash_password
from ..schemas import UserOut, ManagerCreate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/pending", response_model=list[UserOut])
def get_pending_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    """Returnează conturile care așteaptă aprobare (is_active=False)."""
    return db.query(User).filter(User.is_active == False).order_by(User.id.desc()).all()  # noqa: E712


@router.patch("/{user_id}/activate", response_model=UserOut)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    """Aprobă un cont de personal (setează is_active=True)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit.")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.get("/staff", response_model=list[UserOut])
def get_staff_users(
    role: str = None,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
):
    """Returnează personalul (activ + inactiv), filtrat opțional pe rol."""
    q = db.query(User).filter(User.id != current_manager.id)
    if role:
        try:
            q = q.filter(User.role == RoleEnum(role))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Rol invalid: {role}")
    return q.order_by(User.full_name).all()


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
):
    """Dezactivează un cont de personal (setează is_active=False)."""
    if user_id == current_manager.id:
        raise HTTPException(status_code=400, detail="Nu îți poți dezactiva propriul cont.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit.")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
):
    """Șterge definitiv un cont (activ sau în așteptare)."""
    if user_id == current_manager.id:
        raise HTTPException(status_code=400, detail="Nu îți poți șterge propriul cont.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Contul nu a fost găsit.")
    db.delete(user)
    db.commit()


@router.post("/manager", response_model=UserOut, status_code=201)
def create_manager(
    data: ManagerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    """Creează un cont de manager direct (activ imediat, fără aprobare)."""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un cont cu acest email există deja.",
        )
    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=RoleEnum.manager,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
