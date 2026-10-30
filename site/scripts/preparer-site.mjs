import { copyFile, mkdir, readFile, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(scriptDirectory, "..");
const projectRoot = resolve(siteRoot, "..");
const localPython = resolve(projectRoot, ".venv", "bin", "python");
const python = existsSync(localPython) ? localPython : (process.env.PYTHON ?? "python3");
const cataloguePath = "site/src/data/catalogue.json";
const documentsSource = resolve(projectRoot, "documents", "publics");
const documentsTarget = resolve(siteRoot, "public", "documents");

const catalogueArguments = [
  resolve(projectRoot, "scripts", "construire_catalogue.py"),
  "--sortie",
  cataloguePath,
];
if (process.env.GITHUB_ACTIONS) {
  catalogueArguments.push("--allow-missing-internal-files");
}

const result = spawnSync(
  python,
  catalogueArguments,
  { cwd: projectRoot, stdio: "inherit" }
);

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

await rm(documentsTarget, { recursive: true, force: true });
await mkdir(documentsTarget, { recursive: true });

const catalogue = JSON.parse(
  await readFile(resolve(siteRoot, "src", "data", "catalogue.json"), "utf-8")
);
for (const source of Object.values(catalogue.sources)) {
  if (source.visibilite !== "public" || !source.fichier?.startsWith("documents/publics/")) continue;
  const relativeDocument = source.fichier.slice("documents/publics/".length);
  const sourcePath = resolve(projectRoot, source.fichier);
  const targetPath = resolve(documentsTarget, relativeDocument);
  if (!sourcePath.startsWith(documentsSource) || !targetPath.startsWith(documentsTarget)) {
    throw new Error(`Chemin de source public invalide : ${source.fichier}`);
  }
  await mkdir(dirname(targetPath), { recursive: true });
  await copyFile(sourcePath, targetPath);
}
