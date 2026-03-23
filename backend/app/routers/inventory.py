"""
MedicSync — Inventory Router
GET  /inventory             — view current stock levels (any authenticated user).
POST /inventory             — add a new product (inventory_manager only).
PUT  /inventory/{id}        — update stock for a product (inventory_manager only).
GET  /inventory/fefo-alerts — FEFO expiration alerts (inventory_manager only).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import InventoryItem, User
from ..schemas import FefoAlertOut, InventoryItemCreate, InventoryItemOut

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[InventoryItemOut])
def list_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all inventory items sorted by product name.

    🔒 Requires: any authenticated user.
    """
    return db.query(InventoryItem).order_by(InventoryItem.product_name).all()


# IMPORTANT: /fefo-alerts must be defined BEFORE /{item_id} to avoid route conflict
@router.get("/fefo-alerts", response_model=list[FefoAlertOut])
def get_fefo_alerts(
    current_user: User = Depends(require_role("inventory_manager")),
    db: Session = Depends(get_db),
):
    """
    Scan inventory for products approaching or past their expiration date (FEFO policy).

    Returns items ordered by expiration date (First-Expired-First-Out) with severity:
    - **expired**: already past expiration date
    - **critical**: expires within 7 days
    - **warning**: expires within 30 days

    🔒 Requires: **inventory_manager** role.
    """
    today = date.today()
    items = (
        db.query(InventoryItem)
        .order_by(InventoryItem.expiration_date.asc())
        .all()
    )

    alerts = []
    for item in items:
        days_until = (item.expiration_date - today).days

        if days_until < 0:
            severity = "expired"
        elif days_until <= 7:
            severity = "critical"
        elif days_until <= 30:
            severity = "warning"
        else:
            continue  # No alert needed

        alerts.append(
            FefoAlertOut(
                product_name=item.product_name,
                current_stock=item.current_stock,
                expiration_date=item.expiration_date,
                days_until_expiry=days_until,
                severity=severity,
            )
        )

    return alerts


@router.post("/", response_model=InventoryItemOut, status_code=201)
def create_inventory_item(
    item_in: InventoryItemCreate,
    current_user: User = Depends(require_role("inventory_manager")),
    db: Session = Depends(get_db),
):
    """
    Add a new medical supply to the inventory.

    🔒 Requires: **inventory_manager** role.
    """
    item = InventoryItem(
        product_name=item_in.product_name,
        current_stock=item_in.current_stock,
        min_stock_level=item_in.min_stock_level,
        expiration_date=item_in.expiration_date,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(
    item_id: int,
    item_in: InventoryItemCreate,
    current_user: User = Depends(require_role("inventory_manager")),
    db: Session = Depends(get_db),
):
    """
    Update an existing inventory item (stock level, name, expiration, etc.).

    🔒 Requires: **inventory_manager** role.
    """
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

    db.commit()
    db.refresh(item)
    return item

