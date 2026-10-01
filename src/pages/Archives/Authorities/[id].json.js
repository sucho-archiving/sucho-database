

import { authorities, resourcesByAuthority } from "../../../lib/data.js";

export function getStaticPaths() {
  return authorities.map((a) => ({ params: { id: String(a.ID) }, props: { a } }));
}

export function GET({ props }) {
  const { a } = props;
  const body = { ...a, resources: resourcesByAuthority.get(String(a.ID)) ?? [] };
  return new Response(JSON.stringify(body, null, 2), {
    headers: { "Content-Type": "application/json" },
  });
}
