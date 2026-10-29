#!/usr/bin/env python3
"""Génère un CV RenderCV depuis le référentiel professionnel v1.1."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from valider_referentiel import validate_reference


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "referentiel"
PROFILES_DIR = PROJECT_ROOT / "profils_cv" / "metiers"
SECTORS_DIR = PROJECT_ROOT / "profils_cv" / "secteurs"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
BUILD_DIR = PROJECT_ROOT / "build"

yaml = YAML(typ="safe")
output_yaml = YAML()
output_yaml.allow_unicode = True
output_yaml.default_flow_style = False
output_yaml.width = 1000


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Fichier introuvable : {path.relative_to(PROJECT_ROOT)}")
    with path.open(encoding="utf-8") as file:
        return yaml.load(file)


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def as_date(value: Any) -> str:
    return str(value) if value is not None else ""


def date_fields(period: dict[str, Any]) -> dict[str, str]:
    start = as_date(period["debut"])
    end = as_date(period["fin"])
    if len(start) == 4 and len(end) == 4:
        return {"date": f"{start}–{end}"}
    return {"start_date": start, "end_date": end}


def require(identity: dict[str, Any], field: str) -> str:
    value = identity.get(field)
    if not value:
        raise ValueError(f"Champ obligatoire manquant dans donnees/identite.yaml : {field}")
    return str(value)


def detailed_highlight(realization: dict[str, Any], level: int) -> str:
    description = realization["description_factuelle"].strip()
    if level == 2:
        return description
    result = realization["perimetre_ou_resultats"].strip()
    return f"{description} {result}" if result else description


def build_experience_entries(
    profile: dict[str, Any], sector: dict[str, Any], experiences: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rules = {rule["id"]: rule for rule in profile["experiences"]}
    ordered_ids = list(sector.get("experience_priority", []))
    ordered_ids.extend(item_id for item_id in rules if item_id not in ordered_ids)
    entries: list[dict[str, Any]] = []

    for experience_id in ordered_ids:
        rule = rules.get(experience_id)
        if not rule:
            continue
        experience = experiences.get(experience_id)
        if not experience:
            raise ValueError(f"Expérience inconnue dans le profil : {experience_id}")
        level = rule["niveau"]
        entry: dict[str, Any] = {
            "company": experience["organisation"],
            "position": experience["intitule_officiel"],
            "location": experience["lieu"],
            **date_fields(experience["periode"]),
        }
        if level == 1:
            entry["summary"] = experience["resume"]
        else:
            realizations = index_by_id(experience["realisations"])
            entry["highlights"] = [
                detailed_highlight(realizations[realization_id], level)
                for realization_id in rule["realisations"]
            ]
        entries.append(entry)
    return entries


def build_education_entries(profile: dict[str, Any], formations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for rule in profile["education_rules"]:
        formation = formations.get(rule["formation_id"])
        if not formation:
            raise ValueError(f"Formation inconnue dans le profil : {rule['formation_id']}")
        entries.append(
            {
                "institution": formation["etablissement"],
                "area": rule["area"],
                "degree": rule["degree"],
                **date_fields(formation["periode"]),
            }
        )
    return entries


def build_skill_entries(profile: dict[str, Any], skills: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    entries = []
    for group in profile["skill_groups"]:
        names = []
        for skill_id in group["skill_ids"]:
            skill = skills.get(skill_id)
            if not skill:
                raise ValueError(f"Compétence inconnue dans le profil : {skill_id}")
            names.append(skill["nom"])
        entries.append({"label": group["label"], "details": ", ".join(names)})
    return entries


def create_rendercv_document(profile_id: str, sector_id: str) -> tuple[dict[str, Any], str]:
    validate_reference(PROJECT_ROOT)
    identity = load_yaml(REFERENCE_DIR / "identite.yaml")
    experiences = index_by_id(load_yaml(REFERENCE_DIR / "experiences.yaml")["experiences"])
    formations = index_by_id(load_yaml(REFERENCE_DIR / "formations.yaml")["formations"])
    skills = index_by_id(load_yaml(REFERENCE_DIR / "competences.yaml")["competences"])
    profile = load_yaml(PROFILES_DIR / f"{profile_id}.yaml")
    sector = load_yaml(SECTORS_DIR / f"{sector_id}.yaml")

    if profile.get("id") != profile_id or sector.get("id") != sector_id:
        raise ValueError("L’identifiant demandé ne correspond pas au fichier de règles.")

    full_name = f"{require(identity, 'prenom')} {require(identity, 'nom')}"
    document = {
        "cv": {
            "name": full_name,
            "headline": profile["headline"],
            "location": require(identity, "localisation_cible"),
            "email": require(identity, "email"),
            "phone": require(identity, "telephone"),
            "website": require(identity, "portfolio"),
            "social_networks": [{"network": "LinkedIn", "username": require(identity, "linkedin_username")}],
            "sections": {
                "Profil": [profile["summary"]],
                "Expériences": build_experience_entries(profile, sector, experiences),
                "Formation": build_education_entries(profile, formations),
                "Compétences": build_skill_entries(profile, skills),
            },
        },
        "design": {
            "theme": "engineeringresumes",
            "page": {
                "size": "a4", "top_margin": "0.55in", "bottom_margin": "0.55in",
                "left_margin": "0.6in", "right_margin": "0.6in",
                "show_footer": False, "show_top_note": False,
            },
            "typography": {"font_size": {"body": "9.5pt"}},
            "header": {
                "alignment": "left",
                "space_below_name": "0.12cm",
                "connections": {"display_urls_instead_of_usernames": True},
            },
        },
        "locale": {"language": "french"},
    }
    return document, f"CV_Moise_Placier_{profile_id}_{sector_id}"


def install_theme_overrides(yaml_dir: Path) -> None:
    source = TEMPLATES_DIR / "engineeringresumes"
    if source.is_dir():
        shutil.copytree(source, yaml_dir / "engineeringresumes", dirs_exist_ok=True)


def render(input_path: Path, filename: str) -> Path:
    rendercv = PROJECT_ROOT / ".venv" / "bin" / "rendercv"
    command = str(rendercv) if rendercv.is_file() else shutil.which("rendercv")
    if not command:
        raise ValueError("RenderCV est introuvable. Active .venv ou installe RenderCV.")
    paths = {name: BUILD_DIR / name for name in ("pdf", "txt", "html", "png", "typst")}
    for directory in paths.values():
        directory.mkdir(parents=True, exist_ok=True)
    relative = lambda path: Path(os.path.relpath(path, start=input_path.parent))
    pdf_path = paths["pdf"] / f"{filename}.pdf"
    command_line = [
        command, "render", str(input_path),
        "--pdf-path", str(relative(pdf_path)),
        "--markdown-path", str(relative(paths["txt"] / f"{filename}.md")),
        "--html-path", str(relative(paths["html"] / f"{filename}.html")),
        "--png-path", str(relative(paths["png"] / f"{filename}.png")),
        "--typst-path", str(relative(paths["typst"] / f"{filename}.typ")),
    ]
    subprocess.run(command_line, check=True, cwd=PROJECT_ROOT)
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise ValueError("pdftotext est introuvable : impossible de contrôler l’extraction ATS.")
    subprocess.run([pdftotext, "-layout", str(pdf_path), str(paths["txt"] / f"{filename}.txt")], check=True)
    return pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profil", required=True, help="Identifiant de profil, ex. procedes")
    parser.add_argument("--secteur", required=True, help="Identifiant de secteur, ex. agroalimentaire")
    parser.add_argument("--no-render", action="store_true", help="Génère seulement le YAML RenderCV")
    args = parser.parse_args()
    try:
        document, filename = create_rendercv_document(args.profil, args.secteur)
        yaml_dir = BUILD_DIR / "yaml"
        yaml_dir.mkdir(parents=True, exist_ok=True)
        install_theme_overrides(yaml_dir)
        yaml_path = yaml_dir / f"{filename}.yaml"
        with yaml_path.open("w", encoding="utf-8") as file:
            output_yaml.dump(document, file)
        print(f"YAML généré : {yaml_path.relative_to(PROJECT_ROOT)}")
        if not args.no_render:
            print(f"PDF généré : {render(yaml_path, filename).relative_to(PROJECT_ROOT)}")
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
