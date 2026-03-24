"""
MedicSync — Departments Router
GET  /departments     — list all hospital departments.
POST /departments     — create a new department (manager only).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import Department, User
from ..schemas import DepartmentCreate, DepartmentOut

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    """
    Return all hospital departments.
    """
    return db.query(Department).order_by(Department.name).all()


@router.post("/", response_model=DepartmentOut, status_code=201)
def create_department(
    dept_in: DepartmentCreate,
    current_user: User = Depends(require_role("manager")),
    db: Session = Depends(get_db),
):
    """
    Create a new hospital department.

    🔒 Requires: **manager** role.
    """
    existing = db.query(Department).filter(Department.name == dept_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Departamentul '{dept_in.name}' există deja.",
        )

    dept = Department(name=dept_in.name, description=dept_in.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
