# Portfolio local

Le site Astro est généré à partir du catalogue dérivé du référentiel : les YAML restent la seule source de vérité.

```bash
pnpm install
pnpm dev
pnpm build
```

Les commandes préparent automatiquement `src/data/catalogue.json` et copient seulement les documents marqués publics dans `public/documents/`. Ces deux emplacements sont générés et ignorés par Git.

## Publication sur l'hébergement OVHcloud

L'offre OVHcloud STARTER de `moise-placier.com` héberge un site statique : la
seule sortie à publier est `dist/`.

```zsh
cd "/Users/placiermoise/Code/recherche_emploi_2026/site"
pnpm build
```

Dans l'espace client OVHcloud, ouvrez **Hébergement Web → Multisite** et repérez
la ligne `moise-placier.com`. Son champ **Dossier racine** est la destination à
utiliser dans FTP/SSH. Téléversez le **contenu** de `site/dist/` dans ce dossier
(dont `index.html`), et non le dossier `dist` lui-même.

L'hébergement contient actuellement plusieurs sites : ne supposez pas que le
dossier `/www` est celui de ce domaine et n'écrasez pas les autres répertoires.
Après l'envoi, vérifiez `https://moise-placier.com` et
`https://moise-placier.com/mentions-legales/` avec le certificat SSL actif.
