import argparse
import sqlite3

from common import fetch_table, iso_to_sql, write_status_file


def from_baserow():
    rows = fetch_table("status")
    checks = [
        {
            "url": r.get("URL"),
            "checked": iso_to_sql(r.get("Checked")),
            "online": 1 if r.get("Online") else 0,
            "http_status": "",
            "error": r.get("Error") or "",
        }
        for r in rows
        if r.get("URL") and r.get("Checked")
    ]
    path = write_status_file("import-baserow.csv", checks)
    print(f"Wrote {len(checks)} checks to {path}")


def from_sqlite(db_path):
    db = sqlite3.connect(db_path)
    cols = {r[1] for r in db.execute("PRAGMA table_info(online_status)")}
    if not {"resource_ID", "timestamp", "online"} <= cols:
        raise SystemExit(f"online_status has unexpected columns: {sorted(cols)}")
    checks = [
        {"url": url, "checked": ts, "online": online, "http_status": "", "error": ""}
        for url, ts, online in db.execute(
            """SELECT r.collection_url, s.timestamp, s.online
               FROM online_status s JOIN Resources r ON r.ID = s.resource_ID
               WHERE r.collection_url IS NOT NULL ORDER BY s.timestamp"""
        )
    ]
    path = write_status_file("import-datasette.csv", checks)
    print(f"Wrote {len(checks)} checks to {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-baserow", action="store_true")
    parser.add_argument("--from-sqlite", metavar="DB")
    args = parser.parse_args()
    if not (args.from_baserow or args.from_sqlite):
        parser.error("specify --from-baserow and/or --from-sqlite DB")
    if args.from_sqlite:
        from_sqlite(args.from_sqlite)
    if args.from_baserow:
        from_baserow()


if __name__ == "__main__":
    main()
