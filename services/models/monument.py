"""
Monument Model — The core table.
"""
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime, JSON, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from services.database import Base


class Monument(Base):
    __tablename__ = "monuments"

    # Identity
    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    name_local = Column(String(300))

    # Location
    location = Column(String(300), index=True)
    state = Column(String(100), index=True)
    district = Column(String(100))
    country = Column(String(100), default="India", index=True)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)

    # Time period
    built_year_start = Column(Integer, index=True)
    built_year_end = Column(Integer)
    year_display = Column(String(100))
    dynasty = Column(String(200), index=True)
    architecture = Column(String(200), index=True)

    # Classification
    monument_type = Column(String(100), index=True)  # Temple, Fort, Cave, etc.
    unesco_status = Column(String(300))
    unesco_year = Column(Integer)

    # Description
    short_description = Column(Text)
    full_description = Column(Text)
    interesting_facts = Column(JSON, default=list)
    tags = Column(JSON, default=list)

    # Media (JSON arrays of URLs)
    image_urls = Column(JSON, default=list)
    audio_urls = Column(JSON, default=dict)  # {"en": "url", "ta": "url"}

    # Data provenance
    data_source = Column(String(200))
    confidence_score = Column(Float, default=1.0)
    is_published = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    translations = relationship(
        "MonumentTranslation",
        back_populates="monument",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Composite indexes
    __table_args__ = (
        Index("idx_monument_location", "state", "district"),
        Index("idx_monument_type_unesco", "monument_type", "unesco_status"),
    )

    def to_dict(self):
        """Convert to dict for API response."""
        return {
            "id": self.id,
            "name": self.name,
            "name_local": self.name_local,
            "location": self.location,
            "state": self.state,
            "district": self.district,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "built_year": self.year_display or (str(self.built_year_start) if self.built_year_start else None),
            "built_year_start": self.built_year_start,
            "dynasty": self.dynasty,
            "architecture": self.architecture,
            "monument_type": self.monument_type,
            "unesco_status": self.unesco_status,
            "short_description": self.short_description,
            "full_description": self.full_description,
            "interesting_facts": self.interesting_facts or [],
            "tags": self.tags or [],
            "image_urls": self.image_urls or [],
            "audio_urls": self.audio_urls or {},
            "data_source": self.data_source,
        }

    def __repr__(self):
        return f"<Monument {self.id}: {self.name}>"