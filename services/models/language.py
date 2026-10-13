"""
Language Model — Supported Indian languages.
"""
from sqlalchemy import Column, String, Integer, Boolean
from services.database import Base


class Language(Base):
    __tablename__ = "languages"

    code = Column(String(10), primary_key=True)  # "en", "ta", "hi"
    name = Column(String(100), nullable=False)  # "English", "Tamil"
    native_name = Column(String(100))  # "தமிழ்", "हिंदी"
    script = Column(String(50))  # "Latin", "Tamil", "Devanagari"
    tts_supported = Column(Boolean, default=True)
    translation_supported = Column(Boolean, default=True)
    display_order = Column(Integer, default=100)

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "native_name": self.native_name,
            "script": self.script,
            "tts_supported": self.tts_supported,
            "translation_supported": self.translation_supported,
        }

    def __repr__(self):
        return f"<Language {self.code}: {self.name}>"