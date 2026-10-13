"""
Translation Model — Multilingual monument content.
One monument can have translations in many languages.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from services.database import Base


class MonumentTranslation(Base):
    __tablename__ = "monument_translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monument_id = Column(String(64), ForeignKey("monuments.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(10), ForeignKey("languages.code"), nullable=False, index=True)

    # Translated fields
    name = Column(String(300))
    short_description = Column(Text)
    full_description = Column(Text)
    interesting_facts = Column(JSON, default=list)

    # Metadata
    is_verified = Column(String(20), default="auto")  # auto, human, pending
    translator = Column(String(200))  # "Gemini", "Bhashini", "Human"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    monument = relationship("Monument", back_populates="translations")

    def to_dict(self):
        return {
            "language_code": self.language_code,
            "name": self.name,
            "short_description": self.short_description,
            "full_description": self.full_description,
            "interesting_facts": self.interesting_facts or [],
            "is_verified": self.is_verified,
            "translator": self.translator,
        }

    def __repr__(self):
        return f"<Translation {self.monument_id}:{self.language_code}>"