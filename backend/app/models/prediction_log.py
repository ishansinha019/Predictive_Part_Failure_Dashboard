from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(50), ForeignKey("machines.id", ondelete="CASCADE"), index=True, nullable=False)
    part_id = Column(String(50), ForeignKey("parts.id", ondelete="CASCADE"), index=True, nullable=False)
    time_in_service_days = Column(Integer, nullable=False)
    prediction_score = Column(Float, nullable=False)
    recommendation = Column(String(255), nullable=False)
    prediction_timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    # NULL for historical service records that were not produced by a model.
    model_version = Column(String(20), nullable=True)

    machine = relationship("Machine", back_populates="prediction_logs")
    part = relationship("Part", back_populates="prediction_logs")

    __table_args__ = (
        Index("ix_pred_machine_time", "machine_id", "prediction_timestamp"),
        Index("ix_pred_part_score", "part_id", "prediction_score"),
    )

    def __repr__(self):
        return f"<PredictionLog(id={self.id}, machine='{self.machine_id}', part='{self.part_id}', score={self.prediction_score:.2f})>"
