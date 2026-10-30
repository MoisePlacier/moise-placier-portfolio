import rawCatalogue from "../data/catalogue.json";

export type CatalogueObject = Record<string, any> & {
  id: string;
  kind: string;
  type?: string | null;
};

type Source = {
  id: string;
  titre: string;
  format: string;
  visibilite: string;
  fichier?: string;
  auteur?: string;
  libelle_court?: string;
};

type SourceLink = {
  id: string;
  source_id: string;
  relation: string;
  localisation?: string;
};

type Prestations = {
  positionnement: string;
  titre_accueil: string;
  accroche: string;
  disponibilite: string;
  appel_action: { libelle: string; objet_email: string };
  publics: Array<{
    id: string;
    titre: string;
    description: string;
    lien: string;
    libelle_lien: string;
  }>;
  page: {
    surtitre: string;
    titre: string;
    introduction: string;
    expertises: Array<{
      id: string;
      titre: string;
      resume: string;
      prestations: string[];
    }>;
    modalites: {
      titre: string;
      texte: string;
      conclusion: string;
    };
  };
  pied_de_page: string;
};

type MentionsLegales = {
  source_id: string;
  derniere_mise_a_jour: string;
  editeur: {
    nom: string;
    forme_juridique: string;
    adresse: string;
    siren: string;
    siret: string;
    rne: string;
    ape: string;
    activite: string;
  };
  contact: { email: string; telephone: string };
  directeur_publication: string;
  hebergement: { statut: string; texte: string };
  donnees_personnelles: { titre: string; texte: string };
  propriete_intellectuelle: { titre: string; texte: string };
};

type Catalogue = {
  identite: Record<string, string>;
  prestations: Prestations;
  mentions_legales: MentionsLegales;
  objets: Record<string, CatalogueObject>;
  sources: Record<string, Source>;
  index: {
    competence_vers_mobilisations: Record<string, unknown[]>;
    cible_vers_liens: Record<string, SourceLink[]>;
  };
};

export const catalogue = rawCatalogue as unknown as Catalogue;
export const prestations = catalogue.prestations;
export const mentionsLegales = catalogue.mentions_legales;
export const objets = Object.values(catalogue.objets);
export const experiences = objets.filter((item) => item.kind === "experience");
export const formations = objets.filter((item) => item.kind === "formation");
export const projets = objets.filter((item) => item.kind === "projet");
export const competences = objets.filter((item) => item.kind === "competence");

export const competencesParId = Object.fromEntries(
  competences.map((competence) => [competence.id, competence])
);

const months = [
  "janvier", "février", "mars", "avril", "mai", "juin",
  "juillet", "août", "septembre", "octobre", "novembre", "décembre"
];

function formatDate(value: string | number | undefined): string {
  if (!value) return "";
  const text = String(value);
  const match = /^(\d{4})-(\d{2})$/.exec(text);
  return match ? `${months[Number(match[2]) - 1]} ${match[1]}` : text;
}

export function formatPeriod(period?: { debut?: string | number; fin?: string | number }): string {
  if (!period) return "";
  const start = formatDate(period.debut);
  const end = formatDate(period.fin);
  return start && end ? `${start} — ${end}` : start || end;
}

export function publicProofs(objectId: string) {
  return (catalogue.index.cible_vers_liens[objectId] ?? [])
    .map((link) => ({ link, source: catalogue.sources[link.source_id] }))
    .filter(({ source }) => source?.visibilite === "public" && Boolean(source.fichier));
}

export function publicDocumentUrl(source: Source): string | undefined {
  if (!source.fichier) return undefined;
  return withBase(`/${source.fichier.replace(/^documents\/publics\//, "documents/")}`);
}

export function skillsFor(realisation: CatalogueObject): CatalogueObject[] {
  return (realisation.mobilisations ?? [])
    .map((mobilisation: { competence_id: string }) => competencesParId[mobilisation.competence_id])
    .filter(Boolean);
}

export function manifestationsFor(realisation: CatalogueObject): string[] {
  return (realisation.mobilisations ?? []).flatMap((mobilisation: any) =>
    (mobilisation.ressources ?? []).flatMap((resource: any) =>
      (resource.manifestations ?? []).map((manifestation: any) => manifestation.description)
    )
  );
}

export function competenceUseCount(competenceId: string): number {
  return catalogue.index.competence_vers_mobilisations[competenceId]?.length ?? 0;
}

export function byDomain() {
  return competences.reduce<Record<string, CatalogueObject[]>>((groups, competence) => {
    const domain = competence.domaine ?? "Autres";
    (groups[domain] ??= []).push(competence);
    return groups;
  }, {});
}
import { withBase } from "./paths";
