import { geoConicConformal, geoPath, geoContains, geoArea, geoBounds } from "d3-geo";
import oblasts from "../geo/ukraine-oblasts.json";

const REQUIRED = [
  "UA-05", "UA-07", "UA-09", "UA-12", "UA-14", "UA-18", "UA-21", "UA-23", "UA-26",
  "UA-30", "UA-32", "UA-35", "UA-40", "UA-43", "UA-46", "UA-48", "UA-51", "UA-53",
  "UA-56", "UA-59", "UA-61", "UA-63", "UA-65", "UA-68", "UA-71", "UA-74", "UA-77",
];
{
  const present = new Set(oblasts.features.map((f) => f.properties.iso));
  const missing = REQUIRED.filter((iso) => !present.has(iso));
  if (missing.length || present.size !== REQUIRED.length) {
    throw new Error(`The Ukraine map is incomplete. Missing: ${missing.join(", ") || "-"}`);
  }

  for (const f of oblasts.features) {
    if (geoArea(f) > 0.01) throw new Error(`Wrong ring winding order in ${f.properties.iso}`);
  }
}

export const WIDTH = 800;
export const HEIGHT = 540;
const PAD = 12;

export const projection = geoConicConformal()
  .parallels([45, 52])
  .rotate([-31.5, 0])
  .fitExtent(
    [
      [PAD, PAD],
      [WIDTH - PAD, HEIGHT - PAD],
    ],
    oblasts,
  );

export const path = geoPath(projection);
export const features = oblasts.features;
export const byIso = new Map(features.map((f) => [f.properties.iso, f]));

export const outlinePath = features.map((f) => path(f)).join("");

const norm = (s) =>
  String(s ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/['’ʼ`]/g, "")
    .replace(/\s+/g, " ")
    .trim();

const aliasIndex = new Map();
for (const f of features) {
  const { iso, name_en, name_uk, aliases } = f.properties;
  for (const a of [name_en, name_uk, ...aliases]) aliasIndex.set(norm(a), iso);
}

export function oblastFromDistrict(name) {
  const n = norm(name);
  if (!n) return null;
  if (aliasIndex.has(n)) return aliasIndex.get(n);

  const stripped = n.replace(/\b(oblast|region|область|obl\.?)\b/g, "").trim();
  return aliasIndex.get(stripped) ?? null;
}

export function oblastFromPoint(lat, long) {
  if (!Number.isFinite(lat) || !Number.isFinite(long)) return null;
  const ordered = [byIso.get("UA-30"), byIso.get("UA-40"), ...features];
  const hit = ordered.find((f) => geoContains(f, [long, lat]));
  return hit?.properties.iso ?? null;
}

export function locate(a) {
  const lat = parseFloat(a.lat);
  const long = parseFloat(a.long);
  const isoFromPoint = oblastFromPoint(lat, long);
  const isoFromDistrict = oblastFromDistrict(a.district_en) ?? oblastFromDistrict(a.district_ver);
  const iso = isoFromPoint ?? isoFromDistrict;

  const nearDistrict = !isoFromPoint && isoFromDistrict && nearOblast(isoFromDistrict, lat, long);
  const placed = isoFromPoint || nearDistrict;
  return {
    iso,
    point: placed ? projection([long, lat]) : null,
    lat: placed ? lat : null,
    long: placed ? long : null,
  };
}

function nearOblast(iso, lat, long, margin = 0.15) {
  if (!Number.isFinite(lat) || !Number.isFinite(long)) return false;
  const [[w, s], [e, n]] = geoBounds(byIso.get(iso));
  return long >= w - margin && long <= e + margin && lat >= s - margin && lat <= n + margin;
}
