"""
Seed Database — One-time script to populate DB from JSON + defaults.
Run: python -m services.migrations.seed_db
"""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.database import SessionLocal, init_db
from services.repositories.monument_repo import MonumentRepository, LanguageRepository, CategoryRepository


# ============================================
# SUPPORTED LANGUAGES
# ============================================
LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English", "script": "Latin", "display_order": 1},
    {"code": "hi", "name": "Hindi", "native_name": "हिंदी", "script": "Devanagari", "display_order": 2},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்", "script": "Tamil", "display_order": 3},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు", "script": "Telugu", "display_order": 4},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ", "script": "Kannada", "display_order": 5},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം", "script": "Malayalam", "display_order": 6},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা", "script": "Bengali", "display_order": 7},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी", "script": "Devanagari", "display_order": 8},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી", "script": "Gujarati", "display_order": 9},
]


# ============================================
# SEED DATA LOADER
# ============================================
def seed_languages(db):
    repo = LanguageRepository(db)
    n = repo.create_many(LANGUAGES)
    print(f"✅ Languages: {n} new inserted (total: {len(repo.get_all())})")


def seed_monuments(db):
    """Load monuments from data/seed/monuments.json"""
    repo = MonumentRepository(db)

    seed_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "seed", "monuments.json"
    )

    if not os.path.exists(seed_path):
        print(f"⚠️ Seed file not found: {seed_path}")
        return

    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for mid, m in data.items():
        record = {
            "id": mid,
            "name": m.get("name", ""),
            "name_local": m.get("name_local"),
            "location": m.get("location", ""),
            "state": m.get("state"),
            "district": m.get("district"),
            "country": "India",
            "latitude": m.get("latitude"),
            "longitude": m.get("longitude"),
            "built_year_start": m.get("built_year_start"),
            "built_year_end": m.get("built_year_end"),
            "year_display": m.get("built_year", ""),
            "dynasty": m.get("dynasty"),
            "architecture": m.get("architecture"),
            "monument_type": m.get("monument_type", "Monument"),
            "unesco_status": m.get("unesco_status"),
            "short_description": m.get("short_description"),
            "full_description": m.get("full_description"),
            "interesting_facts": m.get("interesting_facts", []),
            "tags": m.get("tags", []),
            "image_urls": m.get("image_urls", []),
            "audio_urls": {},
            "data_source": m.get("data_source", "Manual"),
            "confidence_score": 1.0,
            "is_published": True,
        }
        records.append(record)

    n = repo.bulk_create(records)
    print(f"✅ Monuments: {n} new inserted (total: {repo.count()})")


def seed_categories(db):
    """Seed default architecture and dynasty categories."""
    repo = CategoryRepository(db)

    categories = [
        # Architecture
        {"category_type": "architecture", "value": "Dravidian", "display_name": "Dravidian"},
        {"category_type": "architecture", "value": "Nagara", "display_name": "Nagara"},
        {"category_type": "architecture", "value": "Kalinga", "display_name": "Kalinga"},
        {"category_type": "architecture", "value": "Indo-Islamic", "display_name": "Indo-Islamic"},
        {"category_type": "architecture", "value": "Mughal", "display_name": "Mughal"},
        {"category_type": "architecture", "value": "Rajput", "display_name": "Rajput"},
        {"category_type": "architecture", "value": "Rock-cut", "display_name": "Rock-cut"},
        {"category_type": "architecture", "value": "Buddhist", "display_name": "Buddhist"},
        {"category_type": "architecture", "value": "Sikh", "display_name": "Sikh"},
        {"category_type": "architecture", "value": "Indo-Saracenic", "display_name": "Indo-Saracenic"},

        # Monument types
        {"category_type": "type", "value": "Temple", "display_name": "Temple"},
        {"category_type": "type", "value": "Fort", "display_name": "Fort"},
        {"category_type": "type", "value": "Palace", "display_name": "Palace"},
        {"category_type": "type", "value": "Cave", "display_name": "Cave"},
        {"category_type": "type", "value": "Mausoleum", "display_name": "Mausoleum"},
        {"category_type": "type", "value": "Monument", "display_name": "Monument"},
        {"category_type": "type", "value": "Gurdwara", "display_name": "Gurdwara"},
        {"category_type": "type", "value": "Memorial", "display_name": "Memorial"},
    ]

    n = repo.create_many(categories)
    print(f"✅ Categories: {n} new inserted")


# ============================================
# MAIN
# ============================================
def main():
    print("=" * 60)
    print("HERITAGELENS — DATABASE SEEDER")
    print("=" * 60)

    print("\n📦 Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        print("\n🌐 Seeding languages...")
        seed_languages(db)

        print("\n🏛️ Seeding monuments...")
        seed_monuments(db)

        print("\n📂 Seeding categories...")
        seed_categories(db)

        print("\n" + "=" * 60)
        print("✅ SEED COMPLETE")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()