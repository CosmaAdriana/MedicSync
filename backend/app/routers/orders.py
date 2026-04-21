"""
MedicSync — Orders Router
GET  /orders              — list all supply orders.
POST /orders              — create a new supply order.
PUT  /orders/{id}/status  — change order status (draft → placed → processed → delivered).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_role
from ..models import InventoryItem, Order, OrderItem, OrderStatusEnum, User
from ..schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=list[OrderOut])
def list_orders(
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    total = sum(item.quantity * item.unit_price for item in order_in.items)

    order = Order(
        created_by=current_user.id,
        status=OrderStatusEnum.draft,
        total_amount=total,
    )
    db.add(order)
    db.flush()

    for item_in in order_in.items:
        inv_item = db.query(InventoryItem).filter(InventoryItem.id == item_in.inventory_item_id).first()
        if not inv_item:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produsul cu ID {item_in.inventory_item_id} nu a fost găsit.",
            )
        db.add(OrderItem(
            order_id=order.id,
            inventory_item_id=item_in.inventory_item_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
        ))

    db.commit()
    db.refresh(order)
    return order


# draft → placed → processed → delivered (or placed → rejected)
_VALID_TRANSITIONS = {
    OrderStatusEnum.draft:     [OrderStatusEnum.placed],
    OrderStatusEnum.placed:    [OrderStatusEnum.processed, OrderStatusEnum.rejected],
    OrderStatusEnum.processed: [OrderStatusEnum.delivered],
    OrderStatusEnum.rejected:  [],
    OrderStatusEnum.delivered: [],
}


@router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    new_status: str,
    current_user: User = Depends(require_role("inventory_manager", "manager")),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comanda cu ID {order_id} nu a fost găsită.")

    try:
        target_status = OrderStatusEnum(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status invalid: '{new_status}'. Valori acceptate: {[s.value for s in OrderStatusEnum]}",
        )

    allowed = _VALID_TRANSITIONS.get(order.status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tranziție invalidă: {order.status.value} → {new_status}. "
                   f"Tranziții permise: {[s.value for s in allowed]}",
        )

    order.status = target_status

    if target_status == OrderStatusEnum.delivered:
        for order_item in order.items:
            inv_item = db.query(InventoryItem).filter(
                InventoryItem.id == order_item.inventory_item_id
            ).first()
            if inv_item:
                inv_item.current_stock += order_item.quantity

    db.commit()
    db.refresh(order)
    return order
