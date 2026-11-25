from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.database import get_db
from app.models.enums import WorkOrderPriority, WorkOrderStatus
from app.models.user import User
from app.schemas.work_order import WorkOrderCreate, WorkOrderResponse, WorkOrderUpdate
from app.services.work_order_service import WorkOrderService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_operator),
):
    """
    Create a planned-maintenance work order, typically from a prediction
    (`prediction_id`). The prediction must come from a non-experimental model,
    exceed the maintenance risk threshold and match the machine and part.
    Only one active work order may exist per machine and part.
    """
    return WorkOrderService(db).create(payload, actor)


@router.get("", response_model=List[WorkOrderResponse])
def list_work_orders(
    response: Response,
    status_filter: Optional[WorkOrderStatus] = Query(
        None, alias="status", description="Defaults to pending orders (Open and In_Progress)"
    ),
    machine_id: Optional[str] = Query(None, max_length=50),
    priority: Optional[WorkOrderPriority] = None,
    assigned_technician_id: Optional[int] = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List work orders, most urgent first, with machine, part and technician
    details. The total is returned in the `X-Total-Count` header.
    """
    items, total = WorkOrderService(db).list(
        status=status_filter,
        skip=skip,
        limit=limit,
        machine_id=machine_id,
        priority=priority,
        assigned_technician_id=assigned_technician_id,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
def read_work_order(work_order_id: int, db: Session = Depends(get_db)):
    return WorkOrderService(db).get(work_order_id)


@router.patch("/{work_order_id}", response_model=WorkOrderResponse)
def update_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_operator),
):
    """
    Update status, priority, schedule, notes or assignment.
    Lifecycle: Open -> In_Progress -> Completed, and Open or In_Progress ->
    Cancelled. Completed and Cancelled orders are final. Technicians can only
    assign themselves; administrators can assign any technician.
    """
    return WorkOrderService(db).update(work_order_id, payload, actor)
