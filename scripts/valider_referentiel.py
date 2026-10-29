#!/usr/bin/env python3
"""Valide le référentiel professionnel v1.1 et ses relations inter-objets."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path

from pydantic import ValidationError
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.modeles import ReferenceBundle, load_reference, read_yaml


def duplicate_ids(ids: list[str], label: str, errors: list[str]) -> None:
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        errors.append(f"{label}: IDs dupliqués ({', '.join(duplicates)}).")


def validate_reference(project_root: Path) -> ReferenceBundle:
    bundle = load_reference(project_root)
    errors: list[str] = []
    all_objects: dict[str, str] = {}

    def add(object_id: str, kind: str) -> None:
        if object_id in all_objects:
            errors.append(f"ID dupliqué {object_id} ({kind} et {all_objects[object_id]}).")
        all_objects[object_id] = kind

    for experience in bundle.experiences:
        add(experience.id, "experience")
        for realization in experience.realisations:
            add(realization.id, "realisation")
            for mobilisation in realization.mobilisations:
                add(mobilisation.id, "mobilisation")
                for resource in mobilisation.ressources:
                    for manifestation in resource.manifestations:
                        add(manifestation.id, "manifestation")
    for project in bundle.projets:
        add(project.id, "projet")
        for realization in project.realisations:
            add(realization.id, "realisation")
            for mobilisation in realization.mobilisations:
                add(mobilisation.id, "mobilisation")
                for resource in mobilisation.ressources:
                    for manifestation in resource.manifestations:
                        add(manifestation.id, "manifestation")
    for formation in bundle.formations:
        add(formation.id, "formation")
    for observation in bundle.observations:
        add(observation.id, "observation")
    for learning in bundle.apprentissages:
        add(learning.id, "apprentissage")

    competence_ids = {item.id for item in bundle.competences}
    source_ids = {item.id for item in bundle.sources}
    duplicate_ids([item.id for item in bundle.competences], "compétences", errors)
    duplicate_ids([item.id for item in bundle.sources], "sources", errors)
    duplicate_ids([item.id for item in bundle.liens_sources], "liens documentaires", errors)
    if bundle.mentions_legales.source_id not in source_ids:
        errors.append(
            f"mentions_legales: source inconnue {bundle.mentions_legales.source_id}."
        )

    root = project_root.resolve()
    for source in bundle.sources:
        if source.format == "pdf" and not source.fichier:
            errors.append(f"{source.id}: une source PDF doit référencer un fichier.")
            continue
        if not source.fichier:
            continue
        source_path = (root / source.fichier).resolve()
        try:
            source_path.relative_to(root)
        except ValueError:
            errors.append(f"{source.id}: chemin hors projet ({source.fichier}).")
            continue
        if not source_path.is_file():
            errors.append(f"{source.id}: fichier source introuvable ({source.fichier}).")
            continue
        if source.format == "pdf" and source_path.suffix.lower() != ".pdf":
            errors.append(f"{source.id}: le fichier déclaré comme PDF doit porter l’extension .pdf.")
        if source.sha256:
            actual_hash = sha256(source_path.read_bytes()).hexdigest()
            if actual_hash != source.sha256:
                errors.append(f"{source.id}: empreinte SHA-256 différente du fichier présent.")

    for experience in [*bundle.experiences, *bundle.projets]:
        for realization in experience.realisations:
            if not realization.mobilisations:
                errors.append(f"{realization.id}: aucune mobilisation de compétence.")
            for mobilisation in realization.mobilisations:
                if mobilisation.competence_id not in competence_ids:
                    errors.append(f"{mobilisation.id}: compétence inconnue {mobilisation.competence_id}.")
                for resource in mobilisation.ressources:
                    if resource.ressource_id not in competence_ids:
                        errors.append(f"{mobilisation.id}: ressource inconnue {resource.ressource_id}.")

    for link in bundle.liens_sources:
        if link.source_id not in source_ids:
            errors.append(f"{link.id}: source inconnue {link.source_id}.")
        if link.cible.type != "identite" and link.cible.id not in all_objects and link.cible.id not in competence_ids:
            errors.append(f"{link.id}: cible inconnue {link.cible.id}.")
        if link.contexte_id and link.contexte_id not in all_objects:
            errors.append(f"{link.id}: contexte inconnu {link.contexte_id}.")

    experiences_by_id = {experience.id: experience for experience in bundle.experiences}
    for profile_path in sorted((project_root / "profils_cv" / "metiers").glob("*.yaml")):
        profile = read_yaml(profile_path)
        profile_ids = [rule.get("id") for rule in profile.get("experiences", [])]
        if len(profile_ids) != len(set(profile_ids)):
            errors.append(f"{profile_path.name}: une expérience ne peut être configurée qu’une fois.")
        for rule in profile.get("experiences", []):
            experience_id = rule.get("id")
            level = rule.get("niveau")
            if experience_id not in experiences_by_id:
                errors.append(f"{profile_path.name}: expérience inconnue {experience_id}.")
                continue
            if level not in (1, 2, 3):
                errors.append(f"{profile_path.name}: niveau invalide pour {experience_id}.")
            selected = rule.get("realisations", [])
            if level == 1 and selected:
                errors.append(f"{profile_path.name}: niveau 1 ne sélectionne pas de réalisations ({experience_id}).")
            if level in (2, 3) and not selected:
                errors.append(f"{profile_path.name}: niveau {level} doit sélectionner des réalisations ({experience_id}).")
            known = {item.id for item in experiences_by_id[experience_id].realisations}
            for realization_id in selected:
                if realization_id not in known:
                    errors.append(f"{profile_path.name}: réalisation {realization_id} absente de {experience_id}.")

    if errors:
        raise ValueError("\n".join(f"- {error}" for error in errors))
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--racine", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        validate_reference(args.racine.resolve())
    except (ValueError, ValidationError) as error:
        print(f"Référentiel invalide :\n{error}")
        return 1
    print("Référentiel v1.1 valide : modèles, identifiants et relations cohérents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
