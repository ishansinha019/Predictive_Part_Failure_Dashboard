from typing import List, Optional, Sequence, Tuple

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import WorkOrderPriority, WorkOrderStatus
from app.models.work_order import WorkOrder

_PRIORITY_RANK = case(
    (WorkOrder.priority == WorkOrderPriority.CRITICAL.value, 4),
    (WorkOrder.priority == WorkOrderPriority.HIGH.value, 3),
    (WorkOrder.priority == WorkOrderPriority.MEDIUM.value, 2),
    else_=1,
)


def _with_related():
    return (
        joinedload(WorkOrder.machine),
        joinedload(WorkOrder.part),
        joinedload(WorkOrder.assigned_technician),
    )


class WorkOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, work_order: WorkOrder) -> WorkOrder:
        self.db.add(work_order)
        self.db.flush()
        return work_order

    def get(self, work_order_id: int) -> Optional[WorkOrder]:
        return self.db.scalar(
            select(WorkOrder).options(*_with_related()).where(WorkOrder.id == work_order_id)
        )

    def has_active(self, machine_id: str, part_id: str) -> bool:
        return self.db.scalar(
            select(func.count()).select_from(WorkOrder).where(
                WorkOrder.machine_id == machine_id,
                WorkOrder.part_id == part_id,
                WorkOrder.status.in_([WorkOrderStatus.OPEN.value, WorkOrderStatus.IN_PROGRESS.value]),
            )
        ) > 0

    def has_in_progress(self, machine_id: str, *, excluding_id: int) -> bool:
        return self.db.scalar(
            select(func.count()).select_from(WorkOrder).where(
                WorkOrder.machine_id == machine_id,
                WorkOrder.id != excluding_id,
                WorkOrder.status == WorkOrderStatus.IN_PROGRESS.value,
            )
        ) > 0

    def list(
        self,
        *,
        statuses: Sequence[str],
        skip: int,
        limit: int,
        machine_id: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_technician_id: Optional[int] = None,
    ) -> Tuple[List[WorkOrder], int]:
        """Most urgent first, then newest."""
        conditions = [WorkOrder.status.in_(list(statuses))]
        if machine_id:
            conditions.append(WorkOrder.machine_id == machine_id)
        if priority:
            conditions.append(WorkOrder.priority == priority)
        if assigned_technician_id is not None:
            conditions.append(WorkOrder.assigned_technician_id == assigned_technician_id)

        total = self.db.scalar(select(func.count()).select_from(WorkOrder).where(*conditions))
        items = self.db.scalars(
            select(WorkOrder)
            .options(*_with_related())
            .where(*conditions)
            .order_by(desc(_PRIORITY_RANK), desc(WorkOrder.created_at), desc(WorkOrder.id))
            .offset(skip)
            .limit(limit)
        ).unique().all()
        return list(items), total
