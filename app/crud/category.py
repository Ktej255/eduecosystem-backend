from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category, Tag


class CRUDCategory:
    def get(self, db: Session, id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.id == id).first()

    def get_by_slug(self, db: Session, slug: str) -> Optional[Category]:
        return db.query(Category).filter(Category.slug == slug).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
        return db.query(Category).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: dict) -> Category:
        db_obj = Category(
            name=obj_in["name"],
            slug=obj_in["slug"],
            description=obj_in.get("description"),
            icon=obj_in.get("icon"),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDTag:
    def get(self, db: Session, id: int) -> Optional[Tag]:
        return db.query(Tag).filter(Tag.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Tag]:
        return db.query(Tag).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: dict) -> Tag:
        db_obj = Tag(name=obj_in["name"], slug=obj_in["slug"])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


category = CRUDCategory()
tag = CRUDTag()
