from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.prediction_log import PredictionLog
from app.repositories.machine_repository import latest_prediction_subquery


class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, log: PredictionLog) -> PredictionLog:
        self.db.add(log)
        self.db.flush()
        return log

    def add_all(self, logs: List[PredictionLog]) -> None:
        self.db.add_all(logs)
        self.db.flush()

    def get(self, prediction_id: int) -> Optional[PredictionLog]:
        return self.db.get(PredictionLog, prediction_id)

    def history_for_machine(self, machine_id: str, *, skip: int, limit: int) -> List[PredictionLog]:
        return list(self.db.scalars(
            select(PredictionLog)
            .where(PredictionLog.machine_id == machine_id)
            .order_by(desc(PredictionLog.prediction_timestamp), desc(PredictionLog.id))
            .offset(skip)
            .limit(limit)
        ))

    def latest_per_machine(self) -> List[PredictionLog]:
        """The newest prediction log of every machine."""
        latest = latest_prediction_subquery()
        return list(self.db.scalars(
            select(PredictionLog)
            .join(latest, latest.c.id == PredictionLog.id)
            .order_by(PredictionLog.machine_id)
        ))

    def failure_days_for_part(self, part_id: str, *, min_score: float) -> List[int]:
        return list(self.db.scalars(
            select(PredictionLog.time_in_service_days)
            .where(PredictionLog.part_id == part_id)
            .where(PredictionLog.prediction_score > min_score)
        ))
