import logging
from typing import List, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import (
    ACTIVE_WORK_ORDER_STATUSES,
    MachineStatus,
    UserRole,
    WorkOrderPriority,
    WorkOrderStatus,
)
from app.models.user import User
from app.models.work_order import WorkOrder, utcnow
from app.repositories.machine_repository import MachineRepository
from app.repositories.part_repository import PartRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.work_order_repository import WorkOrderRepository
from app.schemas.work_order import WorkOrderCreate, WorkOrderUpdate
from app.services.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from app.services.prediction_service import MAINTENANCE_THRESHOLD, REPLACEMENT_THRESHOLD

logger = logging.getLogger(__name__)

CRITICAL_THRESHOLD = 0.9

ALLOWED_TRANSITIONS = {
    WorkOrderStatus.OPEN: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.COMPLETED: set(),
    WorkOrderStatus.CANCELLED: set(),
}


def priority_for_risk(risk_score: float) -> WorkOrderPriority:
    if risk_score >= CRITICAL_THRESHOLD:
        return WorkOrderPriority.CRITICAL
    if risk_score > REPLACEMENT_THRESHOLD:
        return WorkOrderPriority.HIGH
    return WorkOrderPriority.MEDIUM


class WorkOrderService:
    """Work order lifecycle: creation from predictions, assignment and status changes."""

    def __init__(self, db: Session):
        self.db = db
        self.work_orders = WorkOrderRepository(db)
        self.machines = MachineRepository(db)
        self.parts = PartRepository(db)
        self.predictions = PredictionRepository(db)
        self.users = UserRepository(db)

    # --- queries ---
    def get(self, work_order_id: int) -> WorkOrder:
        work_order = self.work_orders.get(work_order_id)
        if work_order is None:
            raise NotFoundError(f"Work order {work_order_id} not found")
        return work_order

    def list(
        self,
        *,
        status: Optional[WorkOrderStatus],
        skip: int,
        limit: int,
        machine_id: Optional[str] = None,
        priority: Optional[WorkOrderPriority] = None,
        assigned_technician_id: Optional[int] = None,
    ) -> Tuple[List[WorkOrder], int]:
        """Without a status filter, only pending (Open and In_Progress) orders are listed."""
        statuses = [status.value] if status else list(ACTIVE_WORK_ORDER_STATUSES)
        return self.work_orders.list(
            statuses=statuses,
            skip=skip,
            limit=limit,
            machine_id=machine_id,
            priority=priority.value if priority else None,
            assigned_technician_id=assigned_technician_id,
        )

    # --- commands ---
    def create(self, payload: WorkOrderCreate, actor: User) -> WorkOrder:
        machine = self.machines.get(payload.machine_id)
        if machine is None:
            raise NotFoundError(f"Machine '{payload.machine_id}' not found")
        part = self.parts.get(payload.part_id)
        if part is None:
            raise NotFoundError(f"Part '{payload.part_id}' not found")

        risk_score = None
        if payload.prediction_id is not None:
            risk_score = self._validated_prediction_risk(payload)
        self._validate_assignee(payload.assigned_technician_id, actor)

        if self.work_orders.has_active(payload.machine_id, payload.part_id):
            raise ConflictError("An active work order already exists for this machine and part")

        priority = payload.priority or (
            priority_for_risk(risk_score) if risk_score is not None else WorkOrderPriority.MEDIUM
        )
        work_order = self.work_orders.add(WorkOrder(
            machine_id=payload.machine_id,
            part_id=payload.part_id,
            status=WorkOrderStatus.OPEN.value,
            priority=priority.value,
            estimated_cost=payload.estimated_cost if payload.estimated_cost is not None else part.unit_cost,
            scheduled_date=payload.scheduled_date,
            notes=payload.notes,
            assigned_technician_id=payload.assigned_technician_id,
            prediction_log_id=payload.prediction_id,
            created_by_id=actor.id,
        ))
        self._commit()
        logger.info("Work order %s created for %s/%s by %s", work_order.id, payload.machine_id, payload.part_id, actor.username)
        return self.get(work_order.id)

    def update(self, work_order_id: int, payload: WorkOrderUpdate, actor: User) -> WorkOrder:
        work_order = self.get(work_order_id)
        if actor.role != UserRole.ADMIN.value and work_order.assigned_technician_id not in (None, actor.id):
            raise PermissionDeniedError("This work order is assigned to another technician")

        fields = payload.model_fields_set
        new_status = payload.status if "status" in fields else None
        if work_order.status not in ACTIVE_WORK_ORDER_STATUSES:
            raise ConflictError(f"A {work_order.status} work order can no longer be modified")

        if "assigned_technician_id" in fields:
            self._validate_assignee(payload.assigned_technician_id, actor)
            work_order.assigned_technician_id = payload.assigned_technician_id
        if "priority" in fields:
            work_order.priority = payload.priority.value
        if "scheduled_date" in fields:
            work_order.scheduled_date = payload.scheduled_date
        if "notes" in fields:
            work_order.notes = payload.notes
        if new_status is not None and new_status.value != work_order.status:
            self._change_status(work_order, new_status)

        self._commit()
        logger.info("Work order %s updated by %s", work_order.id, actor.username)
        return self.get(work_order.id)

    # --- helpers ---
    def _validated_prediction_risk(self, payload: WorkOrderCreate) -> float:
        prediction = self.predictions.get(payload.prediction_id)
        if prediction is None:
            raise NotFoundError(f"Prediction {payload.prediction_id} not found")
        if (prediction.machine_id, prediction.part_id) != (payload.machine_id, payload.part_id):
            raise BusinessRuleError("The prediction does not belong to this machine and part")
        if prediction.model_version is None:
            raise BusinessRuleError("Historical service records cannot be used to create a work order")
        if prediction.model_version in settings.experimental_model_versions:
            raise BusinessRuleError(
                f"Predictions from experimental model {prediction.model_version} "
                "cannot be used to create work orders"
            )
        if prediction.prediction_score <= MAINTENANCE_THRESHOLD:
            raise BusinessRuleError("The predicted risk is below the maintenance threshold")
        return prediction.prediction_score

    def _validate_assignee(self, assignee_id: Optional[int], actor: User) -> None:
        if assignee_id is None:
            return
        assignee = self.users.get(assignee_id)
        if assignee is None or assignee.role != UserRole.TECHNICIAN.value:
            raise BusinessRuleError("The assignee must be an existing user with the technician role")
        if actor.role != UserRole.ADMIN.value and assignee_id != actor.id:
            raise PermissionDeniedError("Only administrators can assign work to other technicians")

    def _change_status(self, work_order: WorkOrder, new_status: WorkOrderStatus) -> None:
        current = WorkOrderStatus(work_order.status)
        if new_status not in ALLOWED_TRANSITIONS[current]:
            raise ConflictError(f"Cannot change a work order from {current.value} to {new_status.value}")

        machine = work_order.machine
        work_order.status = new_status.value
        if new_status is WorkOrderStatus.IN_PROGRESS:
            if machine.status == MachineStatus.OPERATIONAL.value:
                machine.status = MachineStatus.MAINTENANCE.value
            return

        if new_status is WorkOrderStatus.COMPLETED:
            now = utcnow()
            work_order.completed_at = now
            machine.last_maintenance_date = now
        if (
            machine.status == MachineStatus.MAINTENANCE.value
            and not self.work_orders.has_in_progress(machine.id, excluding_id=work_order.id)
        ):
            machine.status = MachineStatus.OPERATIONAL.value

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            logger.warning("Work order change rejected by a database constraint", exc_info=True)
            raise ConflictError("The change conflicts with existing data (for example an active work order already exists)")
