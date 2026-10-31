import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? "/moise-placier-portfolio" : "/",
  integrations: [mdx()],
  output: "static",
  build: {
    format: "directory"
  }
});
