"""
Category Model — Architecture styles, dynasties, monument types.
Hierarchical (parent_id self-reference).
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from services.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_type = Column(String(50), nullable=False, index=True)  # architecture, dynasty, type
    value = Column(String(200), nullable=False, index=True)
    display_name = Column(String(200))
    description = Column(String(500))
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    display_order = Column(Integer, default=100)

    # Self-referential relationship
    children = relationship("Category", backref="parent", remote_side=[id])

    def to_dict(self):
        return {
            "id": self.id,
            "category_type": self.category_type,
            "value": self.value,
            "display_name": self.display_name or self.value,
            "description": self.description,
            "parent_id": self.parent_id,
        }

    def __repr__(self):
        return f"<Category {self.category_type}: {self.value}>"