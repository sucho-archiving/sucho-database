import { cpSync, mkdirSync, readFileSync } from "node:fs";

const src = "node_modules/replaywebpage";
const dest = "public/replay";
mkdirSync(dest, { recursive: true });
for (const f of ["ui.js", "sw.js"]) cpSync(`${src}/${f}`, `${dest}/${f}`);

const { version } = JSON.parse(readFileSync(`${src}/package.json`, "utf8"));
console.log(`ReplayWeb.page ${version} -> ${dest}/`);
