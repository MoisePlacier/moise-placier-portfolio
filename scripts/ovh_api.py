#!/usr/bin/env python3
"""Client minimal, en lecture seule, pour l'API OVHcloud.

Le jeton est lu uniquement dans la variable d'environnement OVH_TOKEN.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from pathlib import PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOTS = {
    "v1": "https://api.eu.ovhcloud.com/1.0",
    "v2": "https://api.eu.ovhcloud.com/v2",
}
NAVIGATION_PATH = "__schemas/developer-hub-navigation.json"


class OvhApiError(RuntimeError):
    """Erreur sûre à afficher à la personne utilisant l'outil."""


def api_root(version: str) -> str:
    return API_ROOTS[version]


def safe_relative_path(value: str, *, label: str) -> str:
    """Refuse les URLs complètes et les sorties de l'espace API choisi."""
    path = value.strip().lstrip("/")
    candidate = PurePosixPath(path)
    if not path or ":" in path or ".." in candidate.parts:
        raise OvhApiError(f"{label} invalide : utilisez un chemin relatif à l'API.")
    return path


def fetch_json(url: str, token: str | None = None) -> Any:
    headers = {"Accept": "application/json"}
    if token:
        headers["authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=30, context=tls_context()) as response:
            return json.load(response)
    except HTTPError as error:
        message = ""
        try:
            payload = json.load(error)
            message = payload.get("message") or payload.get("error") or ""
        except (ValueError, TypeError):
            pass
        suffix = f" — {message}" if message else ""
        raise OvhApiError(f"OVHcloud répond HTTP {error.code}{suffix}") from error
    except URLError as error:
        raise OvhApiError(f"Connexion à OVHcloud impossible : {error.reason}") from error


def tls_context() -> ssl.SSLContext:
    """Utilise le magasin système lorsqu'une installation Python n'en trouve pas."""
    defaults = ssl.get_default_verify_paths()
    candidates = (
        os.environ.get("SSL_CERT_FILE"),
        defaults.cafile,
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    )
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return ssl.create_default_context(cafile=candidate)
    return ssl.create_default_context()


def token_from_environment() -> str:
    token = os.environ.get("OVH_TOKEN", "").strip()
    if not token:
        raise OvhApiError(
            "OVH_TOKEN est absent. Définissez-le dans le terminal sans l'écrire dans le dépôt."
        )
    return token


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def print_sections(nodes: list[dict[str, Any]], prefix: str = "", parents: tuple[str, ...] = ()) -> None:
    for node in nodes:
        slug = str(node["slug"])
        path = "/".join((*parents, slug))
        operations = node.get("operationCount", 0)
        print(f"{prefix}{node['name']}  [{path}] — {operations} opérations")
        children = node.get("children", [])
        if children:
            print_sections(children, prefix=f"{prefix}  ", parents=(*parents, slug))


def command_sections(args: argparse.Namespace) -> int:
    document = fetch_json(f"{api_root('v1')}/{NAVIGATION_PATH}")
    if args.json:
        print_json(document)
    else:
        print_sections(document.get("navigation", []))
    return 0


def command_spec(args: argparse.Namespace) -> int:
    section = safe_relative_path(args.section, label="Section")
    query = urlencode({"format": "openapi3"})
    url = f"{api_root(args.version)}/{NAVIGATION_PATH[:-5]}/{section}.json?{query}"
    print_json(fetch_json(url))
    return 0


def command_get(args: argparse.Namespace) -> int:
    path = safe_relative_path(args.path, label="Chemin")
    query_items: dict[str, str] = {}
    for item in args.param:
        if "=" not in item:
            raise OvhApiError("Chaque --param doit être écrit clé=valeur.")
        key, value = item.split("=", 1)
        if not key:
            raise OvhApiError("La clé d'un --param ne peut pas être vide.")
        query_items[key] = value
    query = f"?{urlencode(query_items)}" if query_items else ""
    url = f"{api_root(args.version)}/{path}{query}"
    print_json(fetch_json(url, token_from_environment()))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Découvre et interroge OVHcloud avec OVH_TOKEN (GET uniquement)."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    sections = subcommands.add_parser("sections", help="Liste les sections publiques de l'API.")
    sections.add_argument("--json", action="store_true", help="Affiche le schéma brut en JSON.")
    sections.set_defaults(handler=command_sections)

    spec = subcommands.add_parser("spec", help="Télécharge une spécification OpenAPI 3 de section.")
    spec.add_argument("section", help="Ex. web-cloud/domains")
    spec.add_argument("--version", choices=API_ROOTS, default="v1", help="Version d'API (v1 par défaut).")
    spec.set_defaults(handler=command_spec)

    get = subcommands.add_parser("get", help="Effectue une requête OVHcloud GET authentifiée.")
    get.add_argument("path", help="Ex. /domain ou /hosting/web")
    get.add_argument("--version", choices=API_ROOTS, default="v1", help="Version d'API (v1 par défaut).")
    get.add_argument("--param", action="append", default=[], metavar="CLÉ=VALEUR", help="Paramètre de requête (répétable).")
    get.set_defaults(handler=command_get)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except OvhApiError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
