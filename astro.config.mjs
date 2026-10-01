import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

// https://docs.astro.build/en/reference/configuration-reference/
export default defineConfig({
  // Ändra till den riktiga adressen när sajten ska publiceras.
  site: "https://archives.sucho.org",
  // Om sajten ligger i en undermapp (t.ex. user.github.io/sucho-archives/)
  // sätter du base: "/sucho-archives". Alla länkar går via url() i src/lib/url.js,
  // så inget annat behöver ändras.
  // base: "/sucho-archives",
  trailingSlash: "always",
  integrations: [svelte()],
});
