from typing import Optional

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.prediction_log import PredictionLog


def latest_prediction_subquery():
    """Latest prediction per machine (ties broken by id)."""
    ranked = select(
        PredictionLog.id.label("id"),
        PredictionLog.machine_id.label("machine_id"),
        PredictionLog.prediction_timestamp.label("ts"),
        PredictionLog.prediction_score.label("score"),
        PredictionLog.recommendation.label("recommendation"),
        func.row_number().over(
            partition_by=PredictionLog.machine_id,
            order_by=(desc(PredictionLog.prediction_timestamp), desc(PredictionLog.id)),
        ).label("rn"),
    ).subquery()
    return select(ranked).where(ranked.c.rn == 1).subquery()


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class MachineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, machine_id: str) -> Optional[Machine]:
        return self.db.get(Machine, machine_id)

    def list_with_latest_prediction(
        self,
        *,
        skip: int,
        limit: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "machine_id",
        order: str = "asc",
    ):
        """Returns ((machine, last_updated, risk, recommendation) rows, total matching)."""
        latest = latest_prediction_subquery()
        query = select(
            Machine, latest.c.ts, latest.c.score, latest.c.recommendation
        ).outerjoin(latest, latest.c.machine_id == Machine.id)

        if search:
            query = query.where(Machine.id.ilike(f"%{_escape_like(search)}%", escape="\\"))
        if status:
            query = query.where(Machine.status == status)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))

        sort_column = {
            "machine_id": Machine.id,
            "last_updated": latest.c.ts,
            "risk": latest.c.score,
        }[sort_by]
        direction = desc if order == "desc" else asc
        # Machines without predictions sort last on every database.
        query = query.order_by(direction(sort_column).nulls_last(), asc(Machine.id)).offset(skip).limit(limit)
        return self.db.execute(query).all(), total
