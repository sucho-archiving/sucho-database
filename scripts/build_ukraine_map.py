import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "ne_10m_admin_1_states_provinces.geojson"
OUT = ROOT / "src" / "geo" / "ukraine-oblasts.json"
SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_10m_admin_1_states_provinces.geojson"
)

OBLASTS = {
    "UA-05": ("Vinnytsia Oblast", "Вінницька область", ["vinnytsia", "vinnytsya", "vinnitsa"]),
    "UA-07": ("Volyn Oblast", "Волинська область", ["volyn", "volhynia"]),
    "UA-09": ("Luhansk Oblast", "Луганська область", ["luhansk", "lugansk"]),
    "UA-12": ("Dnipropetrovsk Oblast", "Дніпропетровська область", ["dnipropetrovsk", "dnipro"]),
    "UA-14": ("Donetsk Oblast", "Донецька область", ["donetsk"]),
    "UA-18": ("Zhytomyr Oblast", "Житомирська область", ["zhytomyr"]),
    "UA-21": ("Zakarpattia Oblast", "Закарпатська область", ["zakarpattia", "transcarpathia", "zakarpattya"]),
    "UA-23": ("Zaporizhzhia Oblast", "Запорізька область", ["zaporizhzhia", "zaporizhia", "zaporizhzhya"]),
    "UA-26": ("Ivano-Frankivsk Oblast", "Івано-Франківська область", ["ivano-frankivsk"]),
    "UA-30": ("Kyiv", "Київ", ["kyiv city", "city of kyiv", "kyiv"]),
    "UA-32": ("Kyiv Oblast", "Київська область", ["kyiv oblast", "kyiv region"]),
    "UA-35": ("Kirovohrad Oblast", "Кіровоградська область", ["kirovohrad", "kropyvnytskyi"]),
    "UA-40": ("Sevastopol", "Севастополь", ["sevastopol"]),
    "UA-43": ("Autonomous Republic of Crimea", "Автономна Республіка Крим", ["crimea", "krym"]),
    "UA-46": ("Lviv Oblast", "Львівська область", ["lviv"]),
    "UA-48": ("Mykolaiv Oblast", "Миколаївська область", ["mykolaiv", "mykolayiv"]),
    "UA-51": ("Odesa Oblast", "Одеська область", ["odesa", "odessa"]),
    "UA-53": ("Poltava Oblast", "Полтавська область", ["poltava"]),
    "UA-56": ("Rivne Oblast", "Рівненська область", ["rivne"]),
    "UA-59": ("Sumy Oblast", "Сумська область", ["sumy"]),
    "UA-61": ("Ternopil Oblast", "Тернопільська область", ["ternopil"]),
    "UA-63": ("Kharkiv Oblast", "Харківська область", ["kharkiv"]),
    "UA-65": ("Kherson Oblast", "Херсонська область", ["kherson"]),
    "UA-68": ("Khmelnytskyi Oblast", "Хмельницька область", ["khmelnytskyi", "khmelnytskyy"]),
    "UA-71": ("Cherkasy Oblast", "Черкаська область", ["cherkasy"]),
    "UA-74": ("Chernihiv Oblast", "Чернігівська область", ["chernihiv"]),
    "UA-77": ("Chernivtsi Oblast", "Чернівецька область", ["chernivtsi"]),
}
assert len(OBLASTS) == 27


def fail(msg):
    sys.exit(f"STOP: {msg}")


def signed_area(ring):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:]))


def rewind(geometry):
    polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    for poly in polys:
        for i, ring in enumerate(poly):
            clockwise = signed_area(ring) < 0
            if (i == 0) != clockwise:
                ring.reverse()
    return geometry


def main():
    if not CACHE.exists():
        print("Downloading Natural Earth admin-1 (~40 MB)...")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SOURCE_URL, CACHE)

    source = json.loads(CACHE.read_text(encoding="utf-8"))

    selected = {}
    for f in source["features"]:
        iso = (f["properties"].get("iso_3166_2") or "").strip()
        if iso.startswith("UA-"):
            if iso in selected:
                fail(f"{iso} appears twice in the source")
            selected[iso] = f["geometry"]

    missing = set(OBLASTS) - set(selected)
    extra = set(selected) - set(OBLASTS)
    if missing:
        fail(f"missing from the source: {sorted(missing)}")
    if extra:
        fail(f"unknown UA codes in the source: {sorted(extra)}")
    for iso in ("UA-43", "UA-40"):
        if not selected[iso] or not selected[iso].get("coordinates"):
            fail(f"geometry missing for {OBLASTS[iso][0]}")

    features = [
        {
            "type": "Feature",
            "properties": {"iso": iso, "name_en": en, "name_uk": uk, "aliases": aliases},
            "geometry": selected[iso],
        }
        for iso, (en, uk, aliases) in sorted(OBLASTS.items())
    ]
    tmp = ROOT / ".cache" / "ukraine-raw.geojson"
    tmp.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
                   encoding="utf-8")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["npx", "mapshaper", str(tmp),
         "-simplify", "8%", "keep-shapes", "planar",
         "-clean",
         "-o", str(OUT), "format=geojson", "precision=0.0001"],
        check=True, cwd=ROOT,
    )

    result = json.loads(OUT.read_text(encoding="utf-8"))
    for f in result["features"]:
        rewind(f["geometry"])
    codes = [f["properties"]["iso"] for f in result["features"] if f.get("geometry")]
    if sorted(codes) != sorted(OBLASTS):
        fail(f"units missing after simplification: {sorted(set(OBLASTS) - set(codes))}")
    result["metadata"] = {
        "source": "Natural Earth 10m admin-1 (public domain), selected by ISO 3166-2:UA",
        "note": "All 27 first-level units of Ukraine within internationally recognised borders, "
                "including the Autonomous Republic of Crimea and Sevastopol.",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} kB), "
          f"{len(codes)} units, including Crimea and Sevastopol.")


if __name__ == "__main__":
    main()
