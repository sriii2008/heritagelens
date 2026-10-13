"""
Bulk Import Orchestrator
Combines Wikipedia fetch + CSV import + JSON import.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.database import SessionLocal, init_db
from services.repositories.monument_repo import MonumentRepository


def import_from_json(json_path: str, update_existing: bool = False) -> int:
    """Import monuments from JSON file (list of dicts)."""
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return 0

    print(f"📄 Reading JSON: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both dict and list formats
    if isinstance(data, dict):
        records = []
        for mid, m in data.items():
            m["id"] = mid
            records.append(m)
    else:
        records = data

    db = SessionLocal()
    try:
        repo = MonumentRepository(db)
        inserted = 0
        skipped = 0

        for record in records:
            # Normalize
            record.setdefault("country", "India")
            record.setdefault("monument_type", "Monument")
            record.setdefault("confidence_score", 1.0)
            record.setdefault("is_published", True)

            # Ensure lists
            for field in ["interesting_facts", "tags", "image_urls"]:
                if not isinstance(record.get(field), list):
                    record[field] = []

            if not record.get("audio_urls"):
                record["audio_urls"] = {}

            if not record.get("id") or not record.get("name"):
                skipped += 1
                continue

            existing = repo.get_by_id(record["id"])
            if existing:
                if update_existing:
                    repo.update(record["id"], record)
                else:
                    skipped += 1
            else:
                repo.create(record)
                inserted += 1

        print(f"\n📊 Import Summary:")
        print(f"   ✅ Inserted: {inserted}")
        print(f"   ⏭️  Skipped:  {skipped}")
        print(f"   📈 Total DB: {repo.count()}")
        return inserted

    finally:
        db.close()


def run_bulk_import():
    """Interactive bulk import menu."""
    print("=" * 60)
    print("HERITAGELENS — BULK IMPORT")
    print("=" * 60)
    print("\nAvailable sources:")
    print("  1. data/seed/monuments.json (original seed)")
    print("  2. data/seed/wikipedia_import.json (Wikipedia fetch)")
    print("  3. data/seed/monuments_template.csv (CSV)")
    print("\nUsage:")
    print("  python -m services.importers.bulk_import [filename]")


if __name__ == "__main__":
    init_db()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith(".json"):
            import_from_json(file_path, update_existing="--update" in sys.argv)
        else:
            print("❌ Only .json files supported by this script")
    else:
        run_bulk_import()