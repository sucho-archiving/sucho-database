import {
  authorities,
  resources,
  onlineByResource,
  resourcesByAuthority,
  authorityById,
  authorityLocation,
  authorityName,
  lastStatus,
  stats,
} from "./data.js";
import { features } from "./ukraineMap.js";

const pct = (part, whole) => (whole ? (100 * part) / whole : 0);



const statuses = resources.map((r) => lastStatus(r.ID));
const online = statuses.filter((s) => s === 1).length;
const offline = statuses.filter((s) => s === 0).length;
const checked = online + offline;
const bytes = resources.reduce((sum, r) => sum + (Number(r.wacz_size_bytes) || 0), 0);

export const keyFigures = {
  resources: resources.length,
  authorities: authorities.length,
  online,
  offline,
  checked,
  offlinePct: pct(offline, checked),
  bytes,
  lastCheck: stats.online_status_daily.at(-1)?.date ?? null,
};

export function formatBytes(n) {
  const units = ["B", "kB", "MB", "GB", "TB", "PB"];
  let i = 0;
  while (n >= 1000 && i < units.length - 1) {
    n /= 1000;
    i++;
  }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}



export const onlineOverTime = stats.online_status_daily.map((d) => {
  const total = d.online_count + d.offline_count;
  return { date: d.date, online: d.online_count, offline: d.offline_count, total, pct: pct(d.online_count, total) };
});

const weekStart = (day) => {
  const d = new Date(`${day}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
};
const weekly = new Map();
for (const { day, count } of stats.collection_timeline) {
  const w = weekStart(day);
  weekly.set(w, (weekly.get(w) ?? 0) + count);
}
let running = 0;
export const archivingTimeline = [...weekly]
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([week, count]) => ({ week, count, total: (running += count) }));

const dated = stats.collection_timeline.reduce((s, d) => s + d.count, 0);
const first = stats.collection_timeline[0]?.day;
const firstMonthEnd = first
  ? new Date(new Date(`${first}T00:00:00Z`).getTime() + 30 * 864e5).toISOString().slice(0, 10)
  : null;
export const archivingSummary = {
  first,
  dated,
  undated: resources.length - dated,
  firstMonth: stats.collection_timeline.filter((d) => d.day <= firstMonthEnd).reduce((s, d) => s + d.count, 0),
  busiestWeek: archivingTimeline.reduce((m, w) => (w.count > (m?.count ?? 0) ? w : m), null),
};


function statusBy(keyOf) {
  const groups = new Map();
  for (const r of resources) {
    const a = r.auth_id ? authorityById.get(String(r.auth_id)) : null;
    const key = keyOf(a);
    if (!key) continue;
    const g = groups.get(key) ?? { key, online: 0, offline: 0 };
    const s = lastStatus(r.ID);
    if (s === 1) g.online++;
    else if (s === 0) g.offline++;
    groups.set(key, g);
  }
  return [...groups.values()]
    .map((g) => ({ ...g, checked: g.online + g.offline, onlinePct: pct(g.online, g.online + g.offline) }))
    .filter((g) => g.checked > 0);
}

export const statusByType = statusBy((a) => a?.institution_type).sort(
  (x, y) => x.onlinePct - y.onlinePct,
);

export const MIN_FOR_SHARE = 5;
const byRegion = new Map(
  statusBy((a) => (a ? authorityLocation.get(String(a.ID))?.iso : null)).map((g) => [g.key, g]),
);
export const statusByRegion = features.map((f) => {
  const g = byRegion.get(f.properties.iso) ?? { online: 0, offline: 0, checked: 0, onlinePct: 0 };
  return { ...f.properties, ...g, enough: g.checked >= MIN_FOR_SHARE };
});


export const recentlyOffline = (() => {
  const dates = stats.online_status_daily.map((d) => d.date);
  if (dates.length < 2) return { list: [], from: null, to: null };
  const [prev, last] = dates.slice(-2);
  const list = [];
  for (const r of resources) {
    const checks = onlineByResource[String(r.ID)] ?? [];
    const byDate = new Map(checks);
    if (byDate.get(prev) === 1 && byDate.get(last) === 0) {
      const a = r.auth_id ? authorityById.get(String(r.auth_id)) : null;
      list.push({ r, institution: a ? { id: a.ID, name: authorityName(a) } : null });
    }
  }
  return { list, from: prev, to: last };
})();

export const authoritiesByType = stats.authorities_by_type
  .filter((t) => t.type)
  .map((t) => ({ label: t.type, value: t.count }));

export const mostArchived = authorities
  .map((a) => ({ a, n: resourcesByAuthority.get(String(a.ID))?.length ?? 0 }))
  .filter((x) => x.n > 0)
  .sort((x, y) => y.n - x.n)
  .slice(0, 10);

export const completeness = stats.completeness
  .map((c) => {
    const label = c.completeness ?? "Not assessed";
    return { label: label.charAt(0).toUpperCase() + label.slice(1), value: c.count };
  })
  .sort((x, y) => y.value - x.value);


const has = (fn) => authorities.filter(fn).length;
export const recordCoverage = [
  { label: "Wikidata identifier", value: has((a) => a.qid) },
  { label: "Placed in a region", value: has((a) => authorityLocation.get(String(a.ID))?.iso) },
  { label: "Coordinates", value: has((a) => authorityLocation.get(String(a.ID))?.point) },
  { label: "English name", value: has((a) => a.name_en) },
  { label: "VIAF identifier", value: has((a) => a.VIAF) },
]
  .map((c) => ({ ...c, pct: pct(c.value, authorities.length) }))
  .sort((a, b) => b.pct - a.pct);
