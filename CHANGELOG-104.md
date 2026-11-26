# Changelog — issue #104

## Issue #104 — Build Windows Actualise, version v14

Build de publication build 14 d'Actualise, à partir du commit 1767bfb
(tête de master au moment du build, intégrant les issues #100 à #103).
`version.json` mis à jour (build 14, SHA-256 de l'archive publiée).
Aucun changement de code applicatif : build de release pur, numéro
imposé explicitement en ligne de commande (`--build 14`). Installeur
et archive produits dans `installeur\output` et recopiés dans
`C:\CCW_Share\_derniers_builds\actualise\` par le script — publication
GitHub (Release, push) laissée à Alain.
