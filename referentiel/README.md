# Référentiel professionnel interconnecté — v1.1

Source de vérité unique pour les CV et le futur portfolio. Les objets sont validés par Pydantic ; les liens documentaires sont stockés dans `liens_sources.yaml` et les relations inverses sont dérivées.

Les mobilisations relient une réalisation à une compétence. Les ressources et manifestations sont facultatives et sont enrichies progressivement.

Les dates administratives (`periode`) restent la référence pour les CV et les formations. Pour les expériences, lorsqu’une visualisation doit représenter les lieux réellement fréquentés, `periodes_presence_physique` conserve une ou plusieurs périodes distinctes, avec leur lieu, sans écraser ces dates administratives.

## Sources actuellement prises en charge

Le premier modèle stabilisé est le PDF : `format: pdf`, `visibilite: public` ou `interne`, `fichier` relatif à la racine du projet et empreinte `sha256`.

Le validateur exige la présence du fichier, interdit de sortir du dépôt et vérifie l’empreinte quand elle est renseignée. Une source `format: declaration` peut ne pas avoir de fichier : elle sert uniquement à conserver une information déclarative interne.

Les formats image, page web et Markdown seront ajoutés ultérieurement, avec leurs conventions propres.
