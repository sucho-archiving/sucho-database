import argparse
import sqlite3
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests
from urllib3.exceptions import InsecureRequestWarning

from common import BUILD_DB, ROOT, load_status_into_db, normalize_url, write_status_file

TIMEOUT = 20
WORKERS = 24
USER_AGENT = (
    "Mozilla/5.0 (compatible; SUCHO-status-check/1.0; +https://sucho.org) "
    "checks whether archived cultural heritage sites are still online"
)
ONLINE_CODES = {401, 403, 429}

warnings.simplefilter("ignore", InsecureRequestWarning)
_local = threading.local()


def session():
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers["User-Agent"] = USER_AGENT
    return _local.s


def check(url):
    target = url if "://" in url else f"http://{url}"
    last_error = ""
    for attempt in range(2):
        for verify in (True, False):
            try:
                with session().get(target, timeout=TIMEOUT, allow_redirects=True,
                                   stream=True, verify=verify) as r:
                    ok = r.status_code < 400 or r.status_code in ONLINE_CODES
                    return ok, r.status_code, "" if verify else "SSLError (responded without certificate verification)"
            except requests.exceptions.SSLError as e:
                last_error = f"SSLError: {e}"[:200]
                continue
            except requests.RequestException as e:
                last_error = type(e).__name__
                break
        if attempt == 0:
            time.sleep(3)
    return False, "", last_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(BUILD_DB))
    parser.add_argument("--limit", type=int, help="only check the first N URLs (for testing)")
    args = parser.parse_args()

    db = sqlite3.connect(args.db)
    urls = [u for (u,) in db.execute(
        "SELECT collection_url FROM Resources WHERE collection_url IS NOT NULL ORDER BY ID")]
    db.close()

    unique = {}
    for u in urls:
        unique.setdefault(normalize_url(u), u)
    targets = list(unique.values())[: args.limit]

    now = datetime.now(timezone.utc)
    checked = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Checking {len(targets)} unique URLs ({len(urls)} resources)...")

    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(check, u): u for u in targets}
        for i, f in enumerate(as_completed(futures), 1):
            online, code, error = f.result()
            results.append({"url": futures[f], "checked": checked, "online": int(online),
                            "http_status": code, "error": error})
            if i % 100 == 0 or i == len(targets):
                n_on = sum(r["online"] for r in results)
                print(f"  {i}/{len(targets)}  online: {n_on}  offline: {i - n_on}")

    results.sort(key=lambda r: r["url"])
    if args.limit:
        path = write_status_file("test-run.csv", results, directory=ROOT / "build")
        print(f"Test run finished, see {path}")
        return
    path = write_status_file(f"{now:%Y-%m-%d}.csv", results)
    print(f"Wrote {path}")
    load_status_into_db(args.db)


if __name__ == "__main__":
    main()
