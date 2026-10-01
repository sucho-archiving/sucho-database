import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

export default defineConfig({
  site: "https://www.sucho.org",
  base: "/sucho-database",
  trailingSlash: "always",
  integrations: [svelte()],
});