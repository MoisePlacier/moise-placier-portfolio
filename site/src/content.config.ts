import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const realisations = defineCollection({
  loader: glob({ pattern: "**/*.mdx", base: "./src/content/realisations" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.string(),
    category: z.string(),
    cover: z.string(),
    coverAlt: z.string(),
    tags: z.array(z.string()).default([]),
    featured: z.boolean().default(false)
  })
});

export const collections = { realisations };
