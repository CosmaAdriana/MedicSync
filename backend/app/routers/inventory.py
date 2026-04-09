"""
MedicSync — Inventory Router
GET  /inventory             — view stock (filtered by dept for nurse/doctor/inventory_manager).
POST /inventory             — add a new product (inventory_manager or manager).
PUT  /inventory/{id}        — update stock (inventory_manager or manager).
GET  /inventory/fefo-alerts — FEFO expiration alerts (inventory_manager or manager).
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import InventoryItem, User
from ..schemas import FefoAlertOut, InventoryItemCreate, InventoryItemOut

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=list[InventoryItemOut])
def list_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return inventory items. Nurses/doctors/inventory_managers see only their department.
    Managers see everything.
    """
    query = db.query(InventoryItem)

    if current_user.role.value in ("nurse", "doctor", "inventory_manager") and current_user.department_id:
        query = query.filter(InventoryItem.department_id == current_user.department_id)

    return query.order_by(InventoryItem.product_name).all()


# IMPORTANT: /fefo-alerts must be before /{item_id}
@router.get("/fefo-alerts", response_model=list[FefoAlertOut])
def get_fefo_alerts(
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    """
    FEFO expiration alerts, filtered by department for inventory_manager.
    """
    today = date.today()
    cutoff = today + timedelta(days=30)

    query = (
        db.query(InventoryItem)
        .filter(InventoryItem.expiration_date <= cutoff)
        .order_by(InventoryItem.expiration_date.asc())
    )
    if current_user.role.value == "inventory_manager" and current_user.department_id:
        query = query.filter(InventoryItem.department_id == current_user.department_id)

    alerts = []
    for item in query.all():
        days_until = (item.expiration_date - today).days
        if days_until < 0:
            severity = "expired"
        elif days_until <= 7:
            severity = "critical"
        else:
            severity = "warning"

        alerts.append(FefoAlertOut(
            product_name=item.product_name,
            current_stock=item.current_stock,
            expiration_date=item.expiration_date,
            days_until_expiry=days_until,
            severity=severity,
        ))

    return alerts


@router.post("/", response_model=InventoryItemOut, status_code=201)
def create_inventory_item(
    item_in: InventoryItemCreate,
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    """
    Add a new medical supply. department_id is required.
    """
    item = InventoryItem(
        product_name=item_in.product_name,
        current_stock=item_in.current_stock,
        min_stock_level=item_in.min_stock_level,
        expiration_date=item_in.expiration_date,
        unit_price=item_in.unit_price,
        department_id=item_in.department_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(
    item_id: int,
    item_in: InventoryItemCreate,
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    """Update an existing inventory item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produsul cu ID {item_id} nu a fost găsit.",
        )

    item.product_name = item_in.product_name
    item.current_stock = item_in.current_stock
    item.min_stock_level = item_in.min_stock_level
    item.expiration_date = item_in.expiration_date
    item.unit_price = item_in.unit_price
    if item_in.department_id is not None:
        item.department_id = item_in.department_id

    db.commit()
    db.refresh(item)
    return item
