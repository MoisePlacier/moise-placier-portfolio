#!/usr/bin/env python3
"""Construit le catalogue JSON dérivé utilisé par les futurs CV et portfolio."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from valider_referentiel import validate_reference


ROOT = Path(__file__).resolve().parents[1]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sortie",
        type=Path,
        default=Path("build/catalogue/catalogue.json"),
        help="Chemin de sortie, relatif à la racine du projet par défaut.",
    )
    parser.add_argument(
        "--allow-missing-internal-files",
        action="store_true",
        help="Autorise l'absence des fichiers référencés à visibilité interne.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.sortie if args.sortie.is_absolute() else ROOT / args.sortie
    bundle = validate_reference(
        ROOT, allow_missing_internal_files=args.allow_missing_internal_files
    )
    objects: dict[str, dict] = {}
    realizations: dict[str, dict] = {}
    competence_to_mobilisations: dict[str, list[dict]] = defaultdict(list)

    for item in [*bundle.experiences, *bundle.projets]:
        item_data = item.model_dump(mode="json")
        objects[item.id] = {**item_data, "kind": "experience" if item in bundle.experiences else "projet"}
        for realization in item.realisations:
            realization_data = realization.model_dump(mode="json")
            realizations[realization.id] = {"parent_id": item.id, **realization_data}
            objects[realization.id] = {**realization_data, "kind": "realisation", "parent_id": item.id}
            for mobilisation in realization.mobilisations:
                competence_to_mobilisations[mobilisation.competence_id].append(
                    {"realisation_id": realization.id, "parent_id": item.id, **mobilisation.model_dump(mode="json")}
                )
    for item in bundle.formations:
        objects[item.id] = {**item.model_dump(mode="json"), "kind": "formation"}
    for item in bundle.competences:
        objects[item.id] = {**item.model_dump(mode="json"), "kind": "competence"}
    for item in bundle.observations:
        objects[item.id] = {**item.model_dump(mode="json"), "kind": "observation"}
    for item in bundle.apprentissages:
        objects[item.id] = {**item.model_dump(mode="json"), "kind": "apprentissage"}

    source_to_links: dict[str, list[dict]] = defaultdict(list)
    target_to_links: dict[str, list[dict]] = defaultdict(list)
    for link in bundle.liens_sources:
        data = link.model_dump(mode="json")
        source_to_links[link.source_id].append(data)
        target_to_links[link.cible.id].append(data)

    catalogue = {
        "schema_version": "1.1.0",
        "identite": bundle.identite,
        "prestations": bundle.prestations.model_dump(mode="json"),
        "mentions_legales": bundle.mentions_legales.model_dump(mode="json"),
        "objets": objects,
        "sources": {source.id: source.model_dump(mode="json") for source in bundle.sources},
        "realisations": realizations,
        "index": {
            "competence_vers_mobilisations": dict(competence_to_mobilisations),
            "source_vers_liens": dict(source_to_links),
            "cible_vers_liens": dict(target_to_links),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Catalogue généré : {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
