
export function readParams(keys) {
  const p = new URLSearchParams(window.location.search);
  return Object.fromEntries(keys.map((k) => [k, p.get(k) ?? ""]));
}

export function writeParams(values) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(values)) if (v) p.set(k, v);
  const qs = p.toString();
  history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
}

export const normalize = (s) =>
  String(s ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
