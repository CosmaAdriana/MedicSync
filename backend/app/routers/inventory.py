"""
MedicSync — Inventory Router
GET  /inventory             — view stock (filtered by dept for nurse/doctor/inventory_manager).
POST /inventory             — add a new product (inventory_manager or manager).
PUT  /inventory/{id}        — update stock (inventory_manager or manager).
GET  /inventory/fefo-alerts — FEFO expiration alerts (inventory_manager or manager).
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Department, InventoryItem, StockUsageLog, User
from ..schemas import FefoAlertOut, InventoryItemCreate, InventoryItemOut, ProductConsumptionStats

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
            id=item.id,
            product_name=item.product_name,
            current_stock=item.current_stock,
            expiration_date=item.expiration_date,
            days_until_expiry=days_until,
            severity=severity,
        ))

    return alerts


@router.delete("/{item_id}", status_code=204)
def delete_inventory_item(
    item_id: int,
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    """Delete an inventory item (inventory_manager or manager only)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Produsul cu ID {item_id} nu a fost găsit.")
    if current_user.role.value == "inventory_manager" and current_user.department_id:
        if item.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Nu ai permisiunea să ștergi produse din alt departament.")
    db.delete(item)
    db.commit()


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


@router.patch("/{item_id}/use", response_model=InventoryItemOut)
def use_inventory_item(
    item_id: int,
    quantity: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decrease stock by quantity. Available to all authenticated roles."""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantitatea trebuie să fie pozitivă.")
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Produsul cu ID {item_id} nu a fost găsit.")
    if item.current_stock < quantity:
        raise HTTPException(status_code=400, detail=f"Stoc insuficient ({item.current_stock} disponibil).")
    item.current_stock -= quantity
    log = StockUsageLog(
        inventory_item_id=item_id,
        department_id=current_user.department_id,
        user_id=current_user.id,
        quantity_used=quantity,
        used_at=datetime.utcnow(),
    )
    db.add(log)
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


@router.get("/consumption-stats", response_model=list[ProductConsumptionStats])
def get_consumption_stats(
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    """Consumption stats + order recommendations based on last 30 days usage."""
    now = datetime.utcnow()
    since_30d = now - timedelta(days=30)
    since_7d  = now - timedelta(days=7)

    items = db.query(InventoryItem)
    if current_user.role.value == "inventory_manager" and current_user.department_id:
        items = items.filter(InventoryItem.department_id == current_user.department_id)
    items = items.all()

    dept_map = {d.id: d.name for d in db.query(Department).all()}

    results = []
    for item in items:
        used_30d = db.query(func.sum(StockUsageLog.quantity_used)).filter(
            StockUsageLog.inventory_item_id == item.id,
            StockUsageLog.used_at >= since_30d,
        ).scalar() or 0

        used_7d = db.query(func.sum(StockUsageLog.quantity_used)).filter(
            StockUsageLog.inventory_item_id == item.id,
            StockUsageLog.used_at >= since_7d,
        ).scalar() or 0

        avg_daily_30d = round(used_30d / 30, 2)
        avg_daily_7d  = round(used_7d / 7, 2)
        avg_daily     = avg_daily_7d if used_7d > 0 else avg_daily_30d

        days_until_stockout = None
        if avg_daily > 0:
            days_until_stockout = round((item.current_stock - item.min_stock_level) / avg_daily, 1)

        recommended = max(0, round(avg_daily * 30) - item.current_stock + item.min_stock_level)

        results.append(ProductConsumptionStats(
            inventory_item_id=item.id,
            product_name=item.product_name,
            department_id=item.department_id,
            department_name=dept_map.get(item.department_id),
            total_used_30d=int(used_30d),
            total_used_7d=int(used_7d),
            avg_daily_7d=avg_daily_7d,
            avg_daily_30d=avg_daily_30d,
            current_stock=item.current_stock,
            min_stock_level=item.min_stock_level,
            days_until_stockout=days_until_stockout,
            recommended_order_qty=int(recommended),
            unit_price=item.unit_price,
        ))

    results.sort(key=lambda x: (x.days_until_stockout is None, x.days_until_stockout or 9999))
    return results
