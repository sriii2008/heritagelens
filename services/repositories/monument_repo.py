"""
Monument Repository — All DB queries related to monuments.
Business logic does NOT go here, only data access.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from services.models import Monument, Language, Category, MonumentTranslation


class MonumentRepository:

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # READ
    # ============================================
    def get_by_id(self, monument_id: str) -> Optional[Monument]:
        return self.db.query(Monument).filter(Monument.id == monument_id).first()

    def get_all(self, limit: int = 100, offset: int = 0, only_published: bool = True) -> List[Monument]:
        q = self.db.query(Monument)
        if only_published:
            q = q.filter(Monument.is_published == True)
        return q.order_by(Monument.name).offset(offset).limit(limit).all()

    def count(self, only_published: bool = True) -> int:
        q = self.db.query(func.count(Monument.id))
        if only_published:
            q = q.filter(Monument.is_published == True)
        return q.scalar()

    def search(
        self,
        query: Optional[str] = None,
        state: Optional[str] = None,
        dynasty: Optional[str] = None,
        architecture: Optional[str] = None,
        monument_type: Optional[str] = None,
        unesco_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Monument]:
        q = self.db.query(Monument).filter(Monument.is_published == True)

        if query:
            like = f"%{query}%"
            q = q.filter(or_(
                Monument.name.ilike(like),
                Monument.location.ilike(like),
                Monument.short_description.ilike(like),
            ))
        if state:
            q = q.filter(Monument.state == state)
        if dynasty:
            q = q.filter(Monument.dynasty == dynasty)
        if architecture:
            q = q.filter(Monument.architecture == architecture)
        if monument_type:
            q = q.filter(Monument.monument_type == monument_type)
        if unesco_only:
            q = q.filter(Monument.unesco_status.isnot(None))

        return q.order_by(Monument.name).offset(offset).limit(limit).all()

    def get_nearby(self, lat: float, lng: float, radius_deg: float = 0.5, limit: int = 10) -> List[Monument]:
        """Find monuments within a lat/lng bounding box."""
        return (
            self.db.query(Monument)
            .filter(Monument.is_published == True)
            .filter(Monument.latitude.isnot(None))
            .filter(Monument.longitude.isnot(None))
            .filter(Monument.latitude.between(lat - radius_deg, lat + radius_deg))
            .filter(Monument.longitude.between(lng - radius_deg, lng + radius_deg))
            .limit(limit)
            .all()
        )

    def list_states(self) -> List[str]:
        rows = (
            self.db.query(Monument.state)
            .filter(Monument.state.isnot(None))
            .distinct()
            .order_by(Monument.state)
            .all()
        )
        return [r[0] for r in rows]

    def list_dynasties(self) -> List[str]:
        rows = (
            self.db.query(Monument.dynasty)
            .filter(Monument.dynasty.isnot(None))
            .distinct()
            .order_by(Monument.dynasty)
            .all()
        )
        return [r[0] for r in rows]

    # ============================================
    # WRITE
    # ============================================
    def create(self, data: Dict[str, Any]) -> Monument:
        monument = Monument(**data)
        self.db.add(monument)
        self.db.commit()
        self.db.refresh(monument)
        return monument

    def update(self, monument_id: str, data: Dict[str, Any]) -> Optional[Monument]:
        monument = self.get_by_id(monument_id)
        if not monument:
            return None
        for key, value in data.items():
            if hasattr(monument, key):
                setattr(monument, key, value)
        self.db.commit()
        self.db.refresh(monument)
        return monument

    def delete(self, monument_id: str) -> bool:
        monument = self.get_by_id(monument_id)
        if not monument:
            return False
        self.db.delete(monument)
        self.db.commit()
        return True

    def bulk_create(self, records: List[Dict[str, Any]]) -> int:
        """Insert many records at once. Skips duplicates."""
        inserted = 0
        for record in records:
            if not self.get_by_id(record.get("id")):
                self.db.add(Monument(**record))
                inserted += 1
        self.db.commit()
        return inserted


class LanguageRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Language]:
        return self.db.query(Language).order_by(Language.display_order).all()

    def get_by_code(self, code: str) -> Optional[Language]:
        return self.db.query(Language).filter(Language.code == code).first()

    def create_many(self, languages: List[Dict[str, Any]]) -> int:
        inserted = 0
        for lang in languages:
            if not self.get_by_code(lang["code"]):
                self.db.add(Language(**lang))
                inserted += 1
        self.db.commit()
        return inserted


class CategoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_type(self, category_type: str) -> List[Category]:
        return (
            self.db.query(Category)
            .filter(Category.category_type == category_type)
            .order_by(Category.display_order)
            .all()
        )

    def create_many(self, categories: List[Dict[str, Any]]) -> int:
        inserted = 0
        for cat in categories:
            exists = (
                self.db.query(Category)
                .filter(Category.category_type == cat["category_type"])
                .filter(Category.value == cat["value"])
                .first()
            )
            if not exists:
                self.db.add(Category(**cat))
                inserted += 1
        self.db.commit()
        return inserted