from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(50), ForeignKey("machines.id", ondelete="CASCADE"), index=True, nullable=False)
    part_id = Column(String(50), ForeignKey("parts.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(String(30), default="Open", nullable=False)  # Open, In_Progress, Completed, Cancelled
    priority = Column(String(20), default="Medium", nullable=False)  # Low, Medium, High, Critical
    estimated_cost = Column(Float, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    machine = relationship("Machine", back_populates="work_orders")
    part = relationship("Part", back_populates="work_orders")

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, machine='{self.machine_id}', part='{self.part_id}', status='{self.status}')>"
