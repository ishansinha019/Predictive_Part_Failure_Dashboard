from typing import Optional

from sqlalchemy.orm import Session

from app.models.part import Part


class PartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, part_id: str) -> Optional[Part]:
        return self.db.get(Part, part_id)
