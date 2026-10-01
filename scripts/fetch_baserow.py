import argparse
import sqlite3
from pathlib import Path

from common import (
    BUILD_DB,
    fetch_table,
    iso_to_sql,
    link_ids,
    load_status_into_db,
    option,
    options,
)

RESOURCE_ID_FIELD = "id"


def map_authority(row):
    return {
        "ID": row["id"],
        "qid": row.get("QID") or None,
        "VIAF": str(row["VIAF"]) if row.get("VIAF") else None,
        "name_en": row.get("Name (en)") or None,
        "name_ver": row.get("Name (ver)") or None,
        "institution_type": option(row.get("Institution type (cleaned)"))
        or row.get("Institution type") or None,
        "district_en": option(row.get("District (en - cleaned)"))
        or row.get("District (en)") or None,
        "district_ver": option(row.get("District (ver - cleaned)"))
        or row.get("District (ver)") or None,
        "location_en": row.get("Location (en)") or None,
        "location_ver": row.get("Location (ver)") or None,
        "lat": row.get("Lat") or None,
        "long": row.get("Long") or None,
        "current_status": ", ".join(options(row.get("Status"))) or None,
        "part_of": ",".join(map(str, link_ids(row.get("is Part Of")))) or None,
        "has_part": ",".join(map(str, link_ids(row.get("Has Part")))) or None,
    }


def map_resource(row):
    authorities = link_ids(row.get("Authority records"))
    return {
        "ID": row[RESOURCE_ID_FIELD],
        "uid": row.get("UID") or None,
        "auth_id": str(authorities[0]) if authorities else None,
        "collection_url": row.get("Collection URL") or None,
        "collection_name_en": row.get("Collection Name (en)") or None,
        "collection_name_ver": row.get("Collection Name (ver)") or None,
        "description": row.get("Description") or None,
        "wacz_url": row.get("wacz_link") or None,
        "wacz_file": row.get("wacz") or None,
        "wacz_timestamp": iso_to_sql(row.get("wacz_timestamp")),
        "wacz_size": row.get("wacz_size") or None,
        "wacz_size_bytes": row.get("wacz_size_bytes") or None,
        "completeness": option(row.get("Completness")),
    }


SCHEMA = """
CREATE TABLE Authorities (
    ID INTEGER PRIMARY KEY, qid TEXT, VIAF TEXT, name_en TEXT, name_ver TEXT,
    institution_type TEXT, district_en TEXT, district_ver TEXT,
    location_en TEXT, location_ver TEXT, lat TEXT, long TEXT,
    current_status TEXT, part_of TEXT, has_part TEXT
);
CREATE TABLE Resources (
    ID INTEGER PRIMARY KEY, uid TEXT, auth_id TEXT, collection_url TEXT,
    collection_name_en TEXT, collection_name_ver TEXT, description TEXT,
    wacz_url TEXT, wacz_file TEXT, wacz_timestamp TEXT, wacz_size TEXT, wacz_size_bytes INTEGER, completeness TEXT,
    FOREIGN KEY (auth_id) REFERENCES Authorities (ID)
);
"""


def insert(db, table, rows):
    if not rows:
        return
    cols = list(rows[0])
    db.executemany(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
        [tuple(r[c] for c in cols) for r in rows],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="use the cached responses in .cache/baserow")
    parser.add_argument("--db", default=str(BUILD_DB))
    args = parser.parse_args()

    print("Fetching from Baserow:")
    authorities = [map_authority(r) for r in fetch_table("authorities", args.offline)]
    resources = [map_resource(r) for r in fetch_table("resources", args.offline)]

    skipped = [r for r in resources if not r["collection_url"]]
    resources = [r for r in resources if r["collection_url"]]

    print(f"Building {args.db}:")
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    insert(db, "Authorities", authorities)
    insert(db, "Resources", resources)
    db.commit()
    db.close()
    print(f"  Authorities: {len(authorities)}, Resources: {len(resources)}"
          + (f" ({len(skipped)} without a URL skipped)" if skipped else ""))

    load_status_into_db(db_path)
    print("Done. Next: python3 scripts/export.py")


if __name__ == "__main__":
    main()
