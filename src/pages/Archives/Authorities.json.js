

import {
  authorities,
  resourcesByAuthority,
  lastStatus,
  authorityLocation,
  oblastName,
} from "../../lib/data.js";

export function GET() {
  const items = authorities.map((a) => {
    const res = resourcesByAuthority.get(String(a.ID)) ?? [];
    const { iso } = authorityLocation.get(String(a.ID));
    return {
      id: a.ID,
      name: a.name_en || a.name_ver,
      ver: a.name_en ? a.name_ver : null,
      type: a.institution_type,
      district: a.district_en || a.district_ver,
      oblast: iso,
      oblastName: oblastName(iso),

      s: res.map((r) => lastStatus(r.ID) ?? "?").join(""),
    };
  });
  return new Response(JSON.stringify(items), { headers: { "Content-Type": "application/json" } });
}
