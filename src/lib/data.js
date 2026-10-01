import authorities from "../data/authorities.json";
import resources from "../data/resources.json";
import onlineByResource from "../data/online_status_by_resource.json";
import stats from "../data/stats.json";
import { locate, byIso } from "./ukraineMap.js";

export { authorities, resources, onlineByResource, stats };

export const authorityById = new Map(authorities.map((a) => [String(a.ID), a]));

export const resourcesByAuthority = new Map();
for (const r of resources) {
  const key = String(r.auth_id);
  if (!resourcesByAuthority.has(key)) resourcesByAuthority.set(key, []);
  resourcesByAuthority.get(key).push(r);
}

export const authorityName = (a) => a?.name_en || a?.name_ver || `#${a?.ID}`;

export const lastStatus = (resourceId) => {
  const checks = onlineByResource[String(resourceId)];
  return checks?.length ? checks.at(-1)[1] : null;
};

export const statusClass = (s) => (s === 1 ? "on" : s === 0 ? "off" : "unknown");
export const statusLabel = (s) =>
  s === 1 ? "Online at last check" : s === 0 ? "Offline at last check" : "Not checked";

export const lastCheckDate = stats.online_status_daily.at(-1)?.date ?? null;

export const splitUrl = (u) => {
  const m = String(u).match(/^(?:https?:\/\/)?(?:www\.)?([^/]+)(.*)$/);
  return m ? { host: m[1], path: m[2] === "/" ? "" : m[2] } : { host: u, path: "" };
};

export const authorityLocation = new Map(authorities.map((a) => [String(a.ID), locate(a)]));

export const oblastName = (iso) => byIso.get(iso)?.properties.name_en ?? null;
export const oblastNameUk = (iso) => byIso.get(iso)?.properties.name_uk ?? null;

{

  const outside = authorities.filter(
    (a) => a.lat && a.long && !authorityLocation.get(String(a.ID)).point,
  );
  const unplaced = authorities.filter((a) => !authorityLocation.get(String(a.ID)).iso);
  if (unplaced.length) {
    const names = [...new Set(unplaced.map((a) => a.district_en || a.district_ver || "(empty)"))];
    console.warn(
      `[map] ${unplaced.length} institutions could not be placed in a region. ` +
        `Unrecognised district names: ${names.slice(0, 10).join("; ")}` +
        ` (add them as aliases in scripts/build_ukraine_map.py)`,
    );
  }
  if (outside.length) {
    console.warn(
      `[map] ${outside.length} institutions have coordinates outside Ukraine and are drawn without a point, ` +
        `e.g. ID ${outside.slice(0, 8).map((a) => a.ID).join(", ")}`,
    );
  }
}
