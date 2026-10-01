import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data"


def rows(db, sql, params=()):
    return [dict(r) for r in db.execute(sql, params)]


def table_exists(db, name):
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def write(name, data):
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}  ({path.stat().st_size / 1024:.0f} kB)")


def export_online_status(db):
    if not table_exists(db, "online_status"):
        print("  (no online_status table, skipping)")
        return {}, []

    per_resource = {}
    for r in db.execute(
        """SELECT resource_ID AS rid, DATE(timestamp) AS date, MAX(online) AS online
           FROM online_status GROUP BY rid, date ORDER BY rid, date"""
    ):
        per_resource.setdefault(str(r["rid"]), []).append([r["date"], r["online"]])

    daily = rows(
        db,
        """SELECT DATE(timestamp) AS date,
                  SUM(CASE WHEN online = 0 THEN 1 ELSE 0 END) AS offline_count,
                  SUM(CASE WHEN online = 1 THEN 1 ELSE 0 END) AS online_count
           FROM online_status GROUP BY DATE(timestamp) ORDER BY date""",
    )
    return per_resource, daily


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "build" / "Archives.db"))
    args = parser.parse_args()

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Exporting from {args.db}:")

    authorities = rows(db, "SELECT * FROM Authorities ORDER BY COALESCE(name_en, name_ver)")
    resources = rows(db, "SELECT * FROM Resources ORDER BY ID")
    online_by_resource, online_daily = export_online_status(db)

    write("authorities", authorities)
    write("resources", resources)
    write("online_status_by_resource", online_by_resource)

    write("stats", {
        "counts": {"authorities": len(authorities), "resources": len(resources)},
        "online_status_daily": online_daily,
        "authorities_by_type": rows(
            db,
            """SELECT institution_type AS type, COUNT(*) AS count FROM Authorities
               GROUP BY institution_type ORDER BY count DESC""",
        ),
        "collection_timeline": rows(
            db,
            """SELECT DATE(wacz_timestamp) AS day, COUNT(*) AS count FROM Resources
               WHERE day IS NOT NULL GROUP BY day ORDER BY day""",
        ),
        "completeness": rows(
            db,
            "SELECT completeness, COUNT(*) AS count FROM Resources GROUP BY completeness",
        ),
    })
    print("Done.")


if __name__ == "__main__":
    main()
