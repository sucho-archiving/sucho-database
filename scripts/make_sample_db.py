import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "sample.db"
DB.unlink(missing_ok=True)
db = sqlite3.connect(DB)

db.executescript("""
CREATE TABLE Authorities (ID integer primary key, qid string unique, VIAF string,
  name_en string, name_ver string, institution_type, district_en string,
  district_ver string, lat string, long string, current_status string);
CREATE TABLE Resources (ID INTEGER primary key, auth_id string, collection_url string,
  wacz_url string, wacz_timestamp date, current_status string, completeness string,
  wacz_size_bytes integer,
  FOREIGN KEY (auth_id) REFERENCES Authorities (ID));
CREATE TABLE online_status (ID INTEGER primary key, resource_ID integer,
  timestamp text, online integer);
""")

db.executemany(
    "INSERT INTO Authorities VALUES (?,?,?,?,?,?,?,?,?,?,?)",
    [
        (1, "Q7077703", "147113728", "Odesa Archeological Museum", "Одеський археологічний музей",
         "Museums", "Odesa Oblast", "Оде́ська о́бласть", "46.4847", "30.7412", None),
        (2, "Q4380226", None, None, "Державний архів Житомирської області",
         "Archives", "Zhytomyr Oblast", "Житомирська область", None, None, None),
    ],
)
db.executemany(
    "INSERT INTO Resources (ID, auth_id, collection_url, wacz_url, wacz_timestamp, current_status, completeness) VALUES (?,?,?,?,?,?,?)",
    [
        (10, "1", "http://www.archaeology.odessa.ua/", "https://example.org/a.wacz",
         "2022-03-04 05:09:34", None, "complete"),
        (11, "1", "http://archaeology.odessa.ua/", None, None, None, "partial"),
        (25, "2", "https://www.geshergalicia.org/ukrainian-archives/",
         "https://example.org/b.wacz", "2022-03-04 20:50:46", None, "complete"),
        (26, None, "https://example.org/orphan/", None, None, None, None),
    ],
)

random.seed(1)

TYPES = ["Museums", "Archives", "Libraries", "Religious institutions",
         "Universities", "Art centers", "Theatres"]
OBLASTS = [("Kyiv", "Київ", 50.45, 30.52), ("Kyiv Oblast", "Київська область", 50.08, 29.92),
           ("Lviv Oblast", "Львівська область", 49.84, 24.03),
           ("Kharkiv Oblast", "Харківська область", 49.99, 36.23),
           ("Odesa Oblast", "Одеська область", 46.48, 30.72),
           ("Chernihiv Oblast", "Чернігівська область", 51.49, 31.29),
           ("Poltava Oblast", "Полтавська область", 49.59, 34.55),
           ("Donetsk Oblast", "Донецька область", 47.10, 37.55),
           ("Autonomous Republic of Crimea", "Автономна Республіка Крим", 44.95, 34.10),
           ("Sevastopol", "Севастополь", 44.60, 33.52),
           ("Kherson Oblast", "Херсонська область", 46.64, 32.61)]
auths, res = [], []
rid = 100
for i in range(3, 80):
    t = random.choice(TYPES)
    d_en, d_ver, clat, clong = random.choice(OBLASTS)
    has_coords = random.random() > 0.2
    auths.append((i, f"Q{900000 + i}", None, f"Sample {t[:-1]} no. {i}" if random.random() > 0.15 else None,
                  f"Зразкова установа № {i}", t, d_en, d_ver,
                  str(round(clat + random.uniform(-0.05, 0.05), 4)) if has_coords else None,
                  str(round(clong + random.uniform(-0.05, 0.05), 4)) if has_coords else None, None))
    for _ in range(random.randint(1, 6)):
        day = date(2022, 3, 1) + timedelta(days=random.randint(0, 120))
        res.append((rid, str(i), f"https://example-{i}.org.ua/collection/{rid}/",
                    "https://example.org/x.wacz" if random.random() > 0.3 else None,
                    f"{day} 12:00:00" if random.random() > 0.1 else None, None,
                    random.choice(["complete", "partial", None])))
        rid += 1
db.executemany("INSERT INTO Authorities VALUES (?,?,?,?,?,?,?,?,?,?,?)", auths)
db.executemany("INSERT INTO Resources (ID, auth_id, collection_url, wacz_url, wacz_timestamp, current_status, completeness) VALUES (?,?,?,?,?,?,?)", res)
db.execute("UPDATE Resources SET wacz_size_bytes = abs(random() % 4000000000) WHERE wacz_url IS NOT NULL")

start = date(2024, 9, 1)
all_ids = [10, 11, 25, 26] + [r[0] for r in res]
checks = []
for r_id in all_ids:
    dies = random.random() < 0.45
    cutoff = random.randint(0, 90)
    for d in range(0, 90, 3):
        online = int(not (dies and d >= cutoff) and random.random() > 0.05)
        checks.append((r_id, f"{start + timedelta(days=d)} 03:00:00", online))
db.executemany("INSERT INTO online_status (resource_ID, timestamp, online) VALUES (?,?,?)", checks)
db.commit()
print(f"Created {DB}")
