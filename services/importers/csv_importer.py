"""
CSV Importer — Bulk load monuments from CSV file.
Usage: python -m services.importers.csv_importer data/seed/monuments.csv
"""
import csv
import os
import sys
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.database import SessionLocal, init_db
from services.repositories.monument_repo import MonumentRepository


def _parse_pipe_list(value: str) -> List[str]:
    """Convert 'a|b|c' into ['a', 'b', 'c']"""
    if not value:
        return []
    return [v.strip() for v in value.split("|") if v.strip()]


def _parse_int(value: str):
    """Safely parse int."""
    if not value or value.strip() == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _parse_float(value: str):
    """Safely parse float."""
    if not value or value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _row_to_record(row: Dict[str, str]) -> Dict:
    """Convert CSV row to DB record."""
    return {
        "id": row.get("id", "").strip().lower().replace(" ", "_"),
        "name": row.get("name", "").strip(),
        "name_local": row.get("name_local", "").strip() or None,
        "location": row.get("location", "").strip(),
        "state": row.get("state", "").strip() or None,
        "district": row.get("district", "").strip() or None,
        "country": "India",
        "latitude": _parse_float(row.get("latitude", "")),
        "longitude": _parse_float(row.get("longitude", "")),
        "built_year_start": _parse_int(row.get("built_year_start", "")),
        "built_year_end": _parse_int(row.get("built_year_end", "")),
        "year_display": row.get("year_display", "").strip() or None,
        "dynasty": row.get("dynasty", "").strip() or None,
        "architecture": row.get("architecture", "").strip() or None,
        "monument_type": row.get("monument_type", "").strip() or "Monument",
        "unesco_status": row.get("unesco_status", "").strip() or None,
        "short_description": row.get("short_description", "").strip() or None,
        "full_description": row.get("full_description", "").strip() or None,
        "interesting_facts": _parse_pipe_list(row.get("interesting_facts", "")),
        "tags": _parse_pipe_list(row.get("tags", "")),
        "image_urls": _parse_pipe_list(row.get("image_urls", "")),
        "audio_urls": {},
        "data_source": row.get("data_source", "CSV Import").strip(),
        "confidence_score": 1.0,
        "is_published": True,
    }


def import_from_csv(csv_path: str, update_existing: bool = False) -> Tuple[int, int, int]:
    """
    Import monuments from CSV.
    Returns: (inserted, updated, skipped)
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return (0, 0, 0)

    print(f"📄 Reading CSV: {csv_path}")

    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    db = SessionLocal()
    try:
        repo = MonumentRepository(db)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            total = 0

            for row_num, row in enumerate(reader, start=2):
                total += 1
                try:
                    record = _row_to_record(row)

                    # Validate
                    if not record["id"] or not record["name"]:
                        errors.append(f"Row {row_num}: Missing id or name")
                        skipped += 1
                        continue

                    existing = repo.get_by_id(record["id"])

                    if existing:
                        if update_existing:
                            repo.update(record["id"], record)
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        repo.create(record)
                        inserted += 1

                    if total % 50 == 0:
                        print(f"   Processed {total} rows...")

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)[:100]}")
                    skipped += 1

        print(f"\n📊 Import Summary:")
        print(f"   ✅ Inserted: {inserted}")
        print(f"   🔄 Updated:  {updated}")
        print(f"   ⏭️  Skipped:  {skipped}")
        print(f"   📈 Total DB: {repo.count()}")

        if errors:
            print(f"\n⚠️  {len(errors)} errors:")
            for err in errors[:10]:
                print(f"   - {err}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more")

        return (inserted, updated, skipped)

    finally:
        db.close()


if __name__ == "__main__":
    init_db()

    csv_file = sys.argv[1] if len(sys.argv) > 1 else "data/seed/monuments_template.csv"
    update_flag = "--update" in sys.argv

    print("=" * 60)
    print("HERITAGELENS — CSV IMPORTER")
    print("=" * 60)

    inserted, updated, skipped = import_from_csv(csv_file, update_existing=update_flag)

    print("\n" + "=" * 60)
    print("✅ IMPORT COMPLETE")
    print("=" * 60)