from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.prediction_log import PredictionLog
from app.repositories.machine_repository import MachineRepository
from app.repositories.prediction_repository import PredictionRepository
from app.schemas.machine import MachineSummary
from app.services.exceptions import NotFoundError


class MachineService:
    def __init__(self, db: Session):
        self.machines = MachineRepository(db)
        self.predictions = PredictionRepository(db)

    def list_fleet(
        self,
        *,
        skip: int,
        limit: int,
        search: Optional[str],
        status: Optional[str],
        sort_by: str,
        order: str,
    ) -> Tuple[List[MachineSummary], int]:
        rows, total = self.machines.list_with_latest_prediction(
            skip=skip, limit=limit, search=search, status=status, sort_by=sort_by, order=order
        )
        summaries = [
            MachineSummary(
                machine_id=machine.id,
                machine_type=machine.machine_type,
                status=machine.status,
                last_updated=last_updated,
                latest_risk_score=score,
                latest_recommendation=recommendation,
            )
            for machine, last_updated, score, recommendation in rows
        ]
        return summaries, total

    def history(self, machine_id: str, *, skip: int, limit: int) -> List[PredictionLog]:
        if self.machines.get(machine_id) is None:
            raise NotFoundError(f"Machine '{machine_id}' not found")
        return self.predictions.history_for_machine(machine_id, skip=skip, limit=limit)
