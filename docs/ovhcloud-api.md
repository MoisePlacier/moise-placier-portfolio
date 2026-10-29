# API OVHcloud

Le client `scripts/ovh_api.py` est volontairement limité aux requêtes `GET` : il
permet de découvrir l'API et d'inspecter le compte sans modifier un domaine, un
DNS ou un hébergement.

## Jeton

Créez un jeton avec les droits minimaux nécessaires dans l'espace OVHcloud, puis
définissez-le seulement dans le terminal courant :

```zsh
export OVH_TOKEN='votre-jeton-ovhcloud'
```

Ne le collez ni dans un fichier versionné, ni dans une conversation. Le projet
ignore les fichiers `.env` ; le fichier `.env.example` ne contient qu'un
emplacement fictif.

## Découvrir l'API

```zsh
# Arborescence des sections du Developer Hub (public, sans jeton)
python3 scripts/ovh_api.py sections

# Spécification OpenAPI 3 de la gestion des domaines
python3 scripts/ovh_api.py spec web-cloud/domains > /tmp/ovh-domains-openapi.json

# Même mécanisme pour la version v2 lorsqu'une section est proposée sous /v2
python3 scripts/ovh_api.py spec web-cloud/domains --version v2 > /tmp/ovh-domains-v2-openapi.json
```

## Inspecter les services liés au site

```zsh
# Domaines auxquels le jeton a accès
python3 scripts/ovh_api.py get /domain

# Hébergements Web accessibles
python3 scripts/ovh_api.py get /hosting/web

# Exemple de paramètre de requête
python3 scripts/ovh_api.py get /domain --param page=1
```

Les chemins disponibles et leurs paramètres sont à consulter dans les
spécifications OpenAPI téléchargées. Le programme envoie exactement une requête
à `https://api.eu.ovhcloud.com/1.0/...` avec l'en-tête
`authorization: Bearer $OVH_TOKEN` pour toute commande `get` de version `v1`.
Il n'affiche jamais ce jeton.

Si Python signale une erreur de certificat TLS, installez ou réparez son magasin
de certificats système. Le client garde toujours la vérification TLS activée et
utilise automatiquement les emplacements système usuels lorsqu'ils existent.
