import argparse
import sqlite3
from collections import defaultdict
from urllib.parse import parse_qs, urlparse

import requests

from common import BUILD_DB

ARCHIVE_EXT = (".wacz", ".warc", ".warc.gz")


def replay_source(wacz_url, wacz_file):
    for link in (wacz_url, wacz_file):
        if not link:
            continue
        u = urlparse(link)
        source = parse_qs(u.query).get("source")
        if source:
            return source[0]
        if u.path.lower().endswith(ARCHIVE_EXT):
            return link
    return None


def check(url, origin):
    headers = {"Origin": origin, "Range": "bytes=0-1023"}
    try:
        r = requests.get(url, headers=headers, timeout=30, stream=True)
        r.close()
    except requests.RequestException as e:
        return {"ok": False, "problem": f"unreachable: {type(e).__name__}"}

    allow = r.headers.get("Access-Control-Allow-Origin", "")
    expose = r.headers.get("Access-Control-Expose-Headers", "").lower()
    problems = []
    if r.status_code >= 400:
        problems.append(f"HTTP {r.status_code}")
    if allow not in ("*", origin):
        problems.append(f"CORS missing (Access-Control-Allow-Origin: {allow or '–'})")
    if r.status_code != 206:
        problems.append(f"no Range support (responded {r.status_code}, not 206)")
    if allow and allow != "*" and "content-range" not in expose:
        problems.append("Content-Range is not exposed (Access-Control-Expose-Headers)")
    return {"ok": not problems, "problem": "; ".join(problems)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True, help="the site's origin, e.g. https://archives.sucho.org")
    parser.add_argument("--db", default=str(BUILD_DB))
    parser.add_argument("--limit", type=int, default=3, help="number of files to test per host")
    args = parser.parse_args()

    db = sqlite3.connect(args.db)
    cols = {r[1] for r in db.execute("PRAGMA table_info(Resources)")}
    file_col = "wacz_file" if "wacz_file" in cols else "NULL"
    rows = db.execute(f"SELECT wacz_url, {file_col} FROM Resources").fetchall()

    by_host = defaultdict(list)
    missing = 0
    for wacz_url, wacz_file in rows:
        src = replay_source(wacz_url, wacz_file)
        if src:
            by_host[urlparse(src).netloc].append(src)
        else:
            missing += 1

    print(f"{len(rows)} resources: {len(rows) - missing} with a playable WACZ, {missing} without.\n")
    for host, urls in sorted(by_host.items(), key=lambda kv: -len(kv[1])):
        results = [check(u, args.origin) for u in urls[: args.limit]]
        ok = all(r["ok"] for r in results)
        print(f"{'OK  ' if ok else 'FAIL'}  {host}  ({len(urls)} files)")
        for u, r in zip(urls, results):
            if not r["ok"]:
                print(f"       {u}\n       -> {r['problem']}")
    print("\nSee README (Archive Replay) for how to configure CORS on the file server.")


if __name__ == "__main__":
    main()
