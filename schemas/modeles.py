"""Modèles Pydantic et chargement du référentiel professionnel v1.1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from ruamel.yaml import YAML


yaml = YAML(typ="safe")


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Periode(Model):
    debut: str | int
    fin: str | int
    precision: str | None = None


class PresencePhysique(Model):
    periode: Periode
    lieu: str


class Manifestation(Model):
    id: str
    description: str


class RessourceMobilisee(Model):
    ressource_id: str
    manifestations: list[Manifestation] = Field(default_factory=list)


class Mobilisation(Model):
    id: str
    competence_id: str
    ressources: list[RessourceMobilisee] = Field(default_factory=list)


class Realisation(Model):
    id: str
    description_factuelle: str
    perimetre_ou_resultats: str
    mobilisations: list[Mobilisation] = Field(default_factory=list)
    titre: str | None = None
    attribution: str | None = None


class Experience(Model):
    id: str
    organisation: str
    intitule_officiel: str
    lieu: str
    periode: Periode
    periodes_presence_physique: list[PresencePhysique] = Field(default_factory=list)
    resume: str
    realisations: list[Realisation]
    secteurs: list[str] = Field(default_factory=list)
    type: str | None = None
    contexte: str | None = None
    effectif_analytique: dict[str, Any] | None = None
    points_a_confirmer: list[str] = Field(default_factory=list)


class Projet(Model):
    id: str
    titre: str
    resume: str
    realisations: list[Realisation]
    date: str | int | None = None
    cadre: str | None = None
    equipe: str | None = None
    attribution: dict[str, Any] | None = None
    secteurs: list[str] = Field(default_factory=list)
    description: str | None = None
    liens: list[str] = Field(default_factory=list)
    points_a_confirmer: list[str] = Field(default_factory=list)


class Formation(Model):
    id: str
    etablissement: str
    intitule: str
    periode: Periode
    statut: str | None = None
    domaines: list[str] = Field(default_factory=list)
    resultats: list[str] = Field(default_factory=list)
    resume: str | None = None


class Competence(Model):
    id: str
    nom: str
    domaine: str
    type: Literal["savoir", "savoir_faire", "comportement", "competence_integree"] | None = None
    description: str | None = None


class AppelAction(Model):
    libelle: str
    objet_email: str


class PublicSite(Model):
    id: str
    titre: str
    description: str
    lien: str
    libelle_lien: str


class ExpertisePrestation(Model):
    id: str
    titre: str
    resume: str
    prestations: list[str]


class ModalitesCollaboration(Model):
    titre: str
    texte: str
    conclusion: str


class PagePrestations(Model):
    surtitre: str
    titre: str
    introduction: str
    expertises: list[ExpertisePrestation]
    modalites: ModalitesCollaboration


class Prestations(Model):
    positionnement: str
    titre_accueil: str
    accroche: str
    disponibilite: str
    appel_action: AppelAction
    publics: list[PublicSite]
    page: PagePrestations
    pied_de_page: str


class EditeurLegal(Model):
    nom: str
    forme_juridique: str
    adresse: str | None = None
    siren: str
    siret: str
    rne: str
    ape: str
    activite: str


class ContactLegal(Model):
    email: str
    telephone: str


class HebergementLegal(Model):
    statut: str
    texte: str


class TexteLegal(Model):
    titre: str
    texte: str


class MentionsLegales(Model):
    source_id: str
    derniere_mise_a_jour: str
    editeur: EditeurLegal
    contact: ContactLegal
    directeur_publication: str
    hebergement: HebergementLegal
    donnees_personnelles: TexteLegal
    propriete_intellectuelle: TexteLegal


class Source(Model):
    id: str
    titre: str
    type: str
    format: Literal["pdf", "declaration"]
    visibilite: Literal["public", "interne"]
    fichier: str | None = None
    date: str | None = None
    sha256: str | None = None
    note: str | None = None
    libelle_court: str | None = None
    auteur: str | None = None


class CibleDocumentaire(Model):
    type: Literal[
        "identite", "experience", "realisation", "projet", "formation", "competence",
        "mobilisation", "manifestation", "observation", "apprentissage", "ressource",
    ]
    id: str
    champ: str | None = None


class LienSource(Model):
    id: str
    source_id: str
    cible: CibleDocumentaire
    relation: Literal["documente", "etaye", "evalue", "illustre", "atteste"]
    localisation: str | None = None
    libelle: str | None = None
    extrait: str | None = None
    commentaire: str | None = None
    contexte_id: str | None = None


class Observation(Model):
    id: str
    competence_id: str | None = None
    ressource_id: str | None = None
    contexte_id: str | None = None
    date: str | None = None
    nature: str
    evaluateur: str | None = None
    constat: str


class Apprentissage(Model):
    id: str
    periode: Periode | None = None
    contexte_id: str | None = None
    ressources_concernees: list[str] = Field(default_factory=list)
    nature: str
    description: str


class ReferenceBundle(Model):
    identite: dict[str, Any]
    prestations: Prestations
    mentions_legales: MentionsLegales
    experiences: list[Experience]
    projets: list[Projet]
    formations: list[Formation]
    competences: list[Competence]
    sources: list[Source]
    liens_sources: list[LienSource]
    observations: list[Observation]
    apprentissages: list[Apprentissage]
    projet_professionnel: dict[str, Any]


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return yaml.load(file)


def load_reference(project_root: Path) -> ReferenceBundle:
    data = project_root / "referentiel"
    identity = read_yaml(data / "identite.yaml")
    return ReferenceBundle(
        identite=identity,
        prestations=read_yaml(data / "prestations.yaml")["prestations"],
        mentions_legales=read_yaml(data / "mentions_legales.yaml")["mentions_legales"],
        experiences=read_yaml(data / "experiences.yaml")["experiences"],
        projets=read_yaml(data / "projets.yaml")["projets"],
        formations=read_yaml(data / "formations.yaml")["formations"],
        competences=read_yaml(data / "competences.yaml")["competences"],
        sources=read_yaml(data / "sources.yaml")["sources"],
        liens_sources=read_yaml(data / "liens_sources.yaml")["liens_sources"],
        observations=read_yaml(data / "observations.yaml")["observations"],
        apprentissages=read_yaml(data / "apprentissages.yaml")["apprentissages"],
        projet_professionnel=read_yaml(data / "projet_professionnel.yaml")["projet_professionnel"],
    )
