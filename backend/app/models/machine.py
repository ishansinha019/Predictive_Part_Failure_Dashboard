from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String(50), primary_key=True, index=True)
    machine_type = Column(String(20), nullable=False)  # 'M' (Medium-Duty) or 'H' (Heavy-Duty)
    status = Column(String(30), default="Operational", nullable=False)  # Operational, Maintenance, Offline
    install_date = Column(DateTime, default=datetime.utcnow, nullable=True)
    last_maintenance_date = Column(DateTime, nullable=True)

    prediction_logs = relationship("PredictionLog", back_populates="machine", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="machine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Machine(id='{self.id}', type='{self.machine_type}', status='{self.status}')>"
