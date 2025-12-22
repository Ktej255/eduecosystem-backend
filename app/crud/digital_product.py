from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.digital_product import DigitalProduct
from app.schemas.digital_product import DigitalProductCreate, DigitalProductUpdate

class CRUDDigitalProduct(CRUDBase[DigitalProduct, DigitalProductCreate, DigitalProductUpdate]):
    def get_by_instructor(self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100) -> List[DigitalProduct]:
        return (
            db.query(self.model)
            .filter(DigitalProduct.instructor_id == instructor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

digital_product = CRUDDigitalProduct(DigitalProduct)
