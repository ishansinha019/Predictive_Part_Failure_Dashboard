from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base
import datetime

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    part_id = Column(String, index=True)
    time_in_service_days = Column(Integer)
    prediction_score = Column(Float)
    recommendation = Column(String)
    prediction_timestamp = Column(DateTime, default=datetime.datetime.utcnow)