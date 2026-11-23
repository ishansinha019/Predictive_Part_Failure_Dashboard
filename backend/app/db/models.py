"""
Database models package re-export.
Provides backward compatibility for existing code importing from app.db.models.
"""
from app.db.database import Base
from app.models.user import User
from app.models.machine import Machine
from app.models.part import Part
from app.models.prediction_log import PredictionLog
from app.models.work_order import WorkOrder

__all__ = ["Base", "User", "Machine", "Part", "PredictionLog", "WorkOrder"]
