import csv
import json
import os
import re
import sqlite3
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BUILD_DB = ROOT / "build" / "Archives.db"
STATUS_DIR = ROOT / "status"
CACHE_DIR = ROOT / ".cache" / "baserow"

BASEROW_URL = os.environ.get("BASEROW_URL", "https://baserow.sucho.org")
TABLES = {"authorities": 706, "resources": 570, "status": 554}

STATUS_FIELDS = ["url", "checked", "online", "http_status", "error"]


def load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_token():
    load_dotenv()
    token = os.environ.get("BASEROW_TOKEN")
    if not token:
        raise SystemExit(
            "BASEROW_TOKEN is missing. Add it to a .env file (BASEROW_TOKEN=...) "
            "or run: export BASEROW_TOKEN=..."
        )
    return token


def fetch_table(name, offline=False):
    cache = CACHE_DIR / f"{name}.json"
    if offline:
        if not cache.exists():
            raise SystemExit(f"No cache for {name}. Run without --offline first.")
        return drop_empty_rows(name, json.loads(cache.read_text(encoding="utf-8")))

    token = get_token()
    url = (
        f"{BASEROW_URL}/api/database/rows/table/{TABLES[name]}/"
        "?user_field_names=true&size=200"
    )
    rows = []
    with requests.Session() as s:
        s.headers["Authorization"] = f"Token {token}"
        while url:
            r = s.get(url, timeout=60)
            r.raise_for_status()
            data = r.json()
            rows.extend(data["results"])
            url = data.get("next")
            print(f"  {name}: {len(rows)}/{data['count']}", end="\r")
    print()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return drop_empty_rows(name, rows)


META_FIELDS = {"id", "order"}


def is_empty_value(v):
    if v is None or v is False:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, dict)):
        return len(v) == 0
    return False


def is_empty_row(row):
    return all(is_empty_value(v) for k, v in row.items() if k not in META_FIELDS)


def drop_empty_rows(name, rows):
    kept = [r for r in rows if not is_empty_row(r)]
    if len(kept) < len(rows):
        print(f"  {name}: skipped {len(rows) - len(kept)} empty rows")
    return kept


def option(value):
    if isinstance(value, dict):
        return value.get("value")
    return value or None


def options(value):
    if not value:
        return []
    return [v.get("value") for v in value if isinstance(v, dict)]


def link_ids(value):
    if not value:
        return []
    return [v["id"] for v in value if isinstance(v, dict) and "id" in v]


def iso_to_sql(ts):
    if not ts:
        return None
    return str(ts).replace("T", " ").replace("Z", "")[:19]


def normalize_url(url):
    if not url:
        return ""
    u = str(url).strip()
    u = re.sub(r"^[a-z]+://", "", u, flags=re.I)
    u = re.sub(r"^www\.", "", u, flags=re.I)
    host, _, path = u.partition("/")
    return f"{host.lower()}/{path}".rstrip("/")


def read_status_checks():
    checks = []
    for f in sorted(STATUS_DIR.glob("*.csv")):
        with f.open(newline="", encoding="utf-8") as fh:
            checks.extend(csv.DictReader(fh))
    return checks


def write_status_file(filename, checks, directory=STATUS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=STATUS_FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(checks)
    return path


def load_status_into_db(db_path=BUILD_DB):
    db = sqlite3.connect(db_path)
    by_url = {}
    for (rid, url) in db.execute("SELECT ID, collection_url FROM Resources"):
        by_url.setdefault(normalize_url(url), []).append(rid)

    rows, unmatched = [], set()
    for c in read_status_checks():
        ids = by_url.get(normalize_url(c["url"]))
        if not ids:
            unmatched.add(c["url"])
            continue
        online = 1 if str(c["online"]).lower() in ("1", "true") else 0
        rows.extend((rid, c["checked"], online, c.get("error") or None) for rid in ids)

    db.executescript("""
        DROP TABLE IF EXISTS online_status;
        CREATE TABLE online_status (ID INTEGER PRIMARY KEY, resource_ID INTEGER,
                                    timestamp TEXT, online INTEGER, error TEXT);
    """)
    db.executemany(
        "INSERT INTO online_status (resource_ID, timestamp, online, error) VALUES (?,?,?,?)", rows
    )
    db.execute("CREATE INDEX idx_status_resource ON online_status (resource_ID)")
    db.commit()
    db.close()
    print(f"  online_status: {len(rows)} rows"
          + (f" ({len(unmatched)} URLs in status/ did not match any resource)" if unmatched else ""))
