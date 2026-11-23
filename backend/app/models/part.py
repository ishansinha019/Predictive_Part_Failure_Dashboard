from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship
from app.db.database import Base

class Part(Base):
    __tablename__ = "parts"

    id = Column(String(50), primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # Bearing, Sensor, Valve, Motor, Controller
    name = Column(String(100), nullable=False)
    expected_lifespan_days = Column(Integer, default=500, nullable=False)
    unit_cost = Column(Float, default=1000.0, nullable=False)
    planned_repair_hours = Column(Float, default=16.0, nullable=False)
    unplanned_repair_hours = Column(Float, default=56.0, nullable=False)

    prediction_logs = relationship("PredictionLog", back_populates="part")
    work_orders = relationship("WorkOrder", back_populates="part")

    def __repr__(self):
        return f"<Part(id='{self.id}', name='{self.name}', category='{self.category}')>"
