# HeritageLens Database

## Overview

SQLite database (migratable to PostgreSQL via `DATABASE_URL` env var).

**Location:** `data/heritagelens.db`

## Schema

### `monuments` — Core table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | String (PK) | Slug identifier (e.g., `brihadeeswarar_temple`) |
| `name` | String | Monument name |
| `name_local` | String | Name in local script |
| `location`, `state`, `district` | String | Geographic info |
| `latitude`, `longitude` | Float | GPS coordinates |
| `built_year_start`, `built_year_end` | Integer | Numeric year range |
| `year_display` | String | Human-readable (e.g., "1010 CE") |
| `dynasty`, `architecture`, `monument_type` | String | Classification |
| `unesco_status` | String | UNESCO designation |
| `short_description`, `full_description` | Text | Descriptions |
| `interesting_facts`, `tags` | JSON | Arrays |
| `image_urls`, `audio_urls` | JSON | Media references |
| `data_source`, `confidence_score` | String/Float | Data provenance |
| `is_published` | Boolean | Visibility toggle |

**Indexes:** `id`, `name`, `state`, `dynasty`, `architecture`, `monument_type`, `latitude`, `longitude`, `built_year_start`

### `languages` — Supported Indian languages

| Column | Type |
|--------|------|
| `code` | String (PK) — "en", "ta", "hi" |
| `name`, `native_name` | String |
| `script` | String |
| `tts_supported`, `translation_supported` | Boolean |

### `monument_translations` — Multilingual content

| Column | Type |
|--------|------|
| `monument_id` | FK → monuments.id |
| `language_code` | FK → languages.code |
| `name`, `short_description`, `full_description` | Translated fields |
| `interesting_facts` | JSON |
| `is_verified`, `translator` | Metadata |

### `categories` — Hierarchical classification

| Column | Type |
|--------|------|
| `category_type` | "architecture", "dynasty", "type" |
| `value`, `display_name` | String |
| `parent_id` | FK → categories.id (self-reference) |

## Migration to PostgreSQL

Set env var:
```
DATABASE_URL=postgresql://user:pass@host:5432/heritagelens
```

No code changes needed.

## Backup

```bash
# Backup
cp data/heritagelens.db data/heritagelens.db.backup

# Restore
cp data/heritagelens.db.backup data/heritagelens.db
```