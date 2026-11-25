from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index, text
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import ACTIVE_WORK_ORDER_STATUSES


def utcnow() -> datetime:
    """Naive UTC timestamp, matching the existing DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


_ACTIVE_PREDICATE = "status IN ({})".format(", ".join(f"'{s}'" for s in ACTIVE_WORK_ORDER_STATUSES))


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(50), ForeignKey("machines.id", ondelete="CASCADE"), index=True, nullable=False)
    part_id = Column(String(50), ForeignKey("parts.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(String(30), default="Open", nullable=False, index=True)  # Open, In_Progress, Completed, Cancelled
    priority = Column(String(20), default="Medium", nullable=False)  # Low, Medium, High, Critical
    estimated_cost = Column(Float, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    assigned_technician_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    prediction_log_id = Column(Integer, ForeignKey("prediction_logs.id", ondelete="SET NULL"), index=True, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    machine = relationship("Machine", back_populates="work_orders")
    part = relationship("Part", back_populates="work_orders")
    assigned_technician = relationship("User", foreign_keys=[assigned_technician_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    prediction_log = relationship("PredictionLog")

    __table_args__ = (
        # At most one active work order per machine and part.
        Index(
            "uq_work_orders_active_machine_part",
            "machine_id",
            "part_id",
            unique=True,
            sqlite_where=text(_ACTIVE_PREDICATE),
            postgresql_where=text(_ACTIVE_PREDICATE),
        ),
    )

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, machine='{self.machine_id}', part='{self.part_id}', status='{self.status}')>"
