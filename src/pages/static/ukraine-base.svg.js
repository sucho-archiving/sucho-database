import { WIDTH, HEIGHT, path, features } from "../../lib/ukraineMap.js";

export function GET() {
  const oblastPaths = features
    .map((f) => `<path d="${path(f)}"><title>${f.properties.name_en}</title></path>`)
    .join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}">
<g fill="#34373d" stroke="#26282c" stroke-width="1.2" stroke-linejoin="round">${oblastPaths}</g>
</svg>`;
  return new Response(svg, { headers: { "Content-Type": "image/svg+xml" } });
}
