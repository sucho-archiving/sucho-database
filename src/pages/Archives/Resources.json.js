
import { resources, authorityById, authorityName, lastStatus } from "../../lib/data.js";

export function GET() {
  const items = resources.map((r) => {
    const a = r.auth_id ? authorityById.get(String(r.auth_id)) : null;
    return {
      id: r.ID,
      url: r.collection_url,
      name: r.collection_name_en || r.collection_name_ver || null,
      date: r.wacz_timestamp ? String(r.wacz_timestamp).slice(0, 10) : null,
      inst: a ? authorityName(a) : null,
      iid: a?.ID ?? null,
      s: lastStatus(r.ID),
    };
  });
  return new Response(JSON.stringify(items), { headers: { "Content-Type": "application/json" } });
}
