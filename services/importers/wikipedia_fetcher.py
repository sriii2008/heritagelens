"""
Wikipedia Monument Fetcher (Rate-Limit Safe)
Fetches monument data from Wikipedia API with polite delays and retries.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

WIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "HeritageLens/1.0 (Educational Project; contact@heritagelens.example)"

# Rate limiting: Wikipedia allows ~1 req/sec for unauthenticated
REQUEST_DELAY = 1.2   # seconds between requests
MAX_RETRIES = 3       # retry failed requests
RETRY_DELAY = 5       # seconds to wait before retry


def _wiki_request(params: Dict, retries: int = MAX_RETRIES) -> Optional[Dict]:
    """Make a Wikipedia API request with retry on rate limit."""
    params["format"] = "json"
    params["formatversion"] = "2"
    url = WIKI_API + "?" + urllib.parse.urlencode(params)

    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
                time.sleep(REQUEST_DELAY)  # polite delay after success
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = RETRY_DELAY * (attempt + 1)
                print(f"   ⏳ Rate limited. Waiting {wait}s (attempt {attempt + 1}/{retries})...")
                time.sleep(wait)
            else:
                print(f"   ⚠️ HTTP {e.code}: {e.reason}")
                time.sleep(2)
        except Exception as e:
            print(f"   ⚠️ Request failed: {e}")
            time.sleep(2)

    return None


def search_wikipedia(query: str) -> Optional[str]:
    """Search Wikipedia, return best matching title."""
    data = _wiki_request({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,
    })
    if not data:
        return None
    results = data.get("query", {}).get("search", [])
    return results[0]["title"] if results else None


def fetch_page_summary(title: str) -> Optional[Dict]:
    """Fetch page summary via REST API."""
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
                time.sleep(REQUEST_DELAY)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = RETRY_DELAY * (attempt + 1)
                print(f"   ⏳ Summary rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                return None
        except Exception:
            time.sleep(2)

    return None


def fetch_page_coordinates(title: str) -> Optional[Dict]:
    """Fetch page coordinates."""
    data = _wiki_request({
        "action": "query",
        "titles": title,
        "prop": "coordinates",
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", [])
    if pages and "coordinates" in pages[0]:
        coords = pages[0]["coordinates"][0]
        return {"lat": coords.get("lat"), "lon": coords.get("lon")}
    return None


def fetch_page_images(title: str, limit: int = 3) -> List[str]:
    """Fetch primary images from Wikipedia page."""
    data = _wiki_request({
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "piprop": "original",
    })
    if not data:
        return []

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return []

    page = pages[0]
    urls = []
    if "original" in page:
        urls.append(page["original"].get("source", ""))

    return [u for u in urls if u]


def build_monument_record(query: str) -> Optional[Dict]:
    """Build a monument record from Wikipedia."""
    print(f"🔍 Searching: {query}")

    title = search_wikipedia(query)
    if not title:
        print(f"   ❌ Not found")
        return None

    print(f"   📄 Found: {title}")

    summary = fetch_page_summary(title)
    if not summary:
        print(f"   ⚠️ No summary")
        return None

    coords = fetch_page_coordinates(title)
    images = fetch_page_images(title)

    record = {
        "id": title.lower().replace(" ", "_").replace(",", "").replace("'", "").replace("(", "").replace(")", ""),
        "name": title,
        "location": summary.get("description", ""),
        "latitude": coords.get("lat") if coords else None,
        "longitude": coords.get("lon") if coords else None,
        "short_description": summary.get("extract", "")[:500],
        "image_urls": images,
        "data_source": "Wikipedia",
    }

    print(f"   ✅ Ready")
    return record


def fetch_from_wikipedia(queries: List[str]) -> List[Dict]:
    """Fetch multiple monuments, with progress tracking and resume."""
    results = []
    failed = []

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query}")
        try:
            record = build_monument_record(query)
            if record:
                results.append(record)
            else:
                failed.append(query)
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            failed.append(query)

    if failed:
        print(f"\n⚠️ Failed: {len(failed)}")
        for f in failed:
            print(f"   - {f}")

    return results


def save_to_json(records: List[Dict], output_path: str, append: bool = True):
    """Save records to JSON file (append by default)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    existing = []
    if append and os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []

    # Merge by id
    existing_ids = {r.get("id") for r in existing}
    merged = existing + [r for r in records if r.get("id") not in existing_ids]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved {len(records)} new records (total in file: {len(merged)})")
    print(f"📁 File: {output_path}")


def load_queries_from_file(path: str) -> List[str]:
    """Load monument names from a text file (one per line)."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m services.importers.wikipedia_fetcher 'Monument 1' 'Monument 2' ...")
        print("  python -m services.importers.wikipedia_fetcher --file data/seed/monument_list.txt")
        sys.exit(1)

    print("=" * 60)
    print("HERITAGELENS — WIKIPEDIA FETCHER")
    print("=" * 60)

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("❌ Specify a file path")
            sys.exit(1)
        queries = load_queries_from_file(sys.argv[2])
        print(f"📄 Loaded {len(queries)} monument names from {sys.argv[2]}")
    else:
        queries = sys.argv[1:]

    print(f"🎯 Will fetch {len(queries)} monuments")
    print(f"⏱️  Estimated time: ~{len(queries) * 5} seconds\n")

    records = fetch_from_wikipedia(queries)

    if records:
        output = "data/seed/wikipedia_import.json"
        save_to_json(records, output, append=True)
        print(f"\n✅ Fetched {len(records)} / {len(queries)}")
    else:
        print("\n⚠️ No records fetched")