import { defineConfig } from "astro/config";

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? "/moise-placier-portfolio" : "/",
  output: "static",
  build: {
    format: "directory"
  }
});
