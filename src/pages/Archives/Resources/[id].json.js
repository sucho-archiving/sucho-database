
import { resources, onlineByResource } from "../../../lib/data.js";

export function getStaticPaths() {
  return resources.map((r) => ({ params: { id: String(r.ID) }, props: { r } }));
}

export function GET({ props }) {
  const { r } = props;
  const body = { ...r, online_status: onlineByResource[String(r.ID)] ?? [] };
  return new Response(JSON.stringify(body, null, 2), {
    headers: { "Content-Type": "application/json" },
  });
}
