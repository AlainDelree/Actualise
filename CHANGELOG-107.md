# Changelog — issue #107

## Issue #107 — Changelog manquant du build 15 (rattrapage de l'issue #106)

Build de publication build 15 d'Actualise, à partir du commit e785c6a
(tête de master au moment du build, premier build contenant l'issue
#105). `version.json` mis à jour (build 15, SHA-256 de l'archive
7d48474097eb28dca44ac331a3e81e01baa70ca86377ce2bbab9ba8008b65014).
Aucun changement de code applicatif : build de release pur, numéro
imposé explicitement en ligne de commande (`--build 15`). Installeur
(20 690 827 octets) et archive (20 608 285 octets) produits et recopiés
par le script dans `C:\CCW_Share\_derniers_builds\actualise\`.

Essai Windows réussi sur le PC fixe, avec Actualise 15 installé : mise
à jour d'un jeu (Scrabble v15), « Bascule reussie », `build_installe`
réécrit, zone d'attente vide ensuite (le `.sha256` est bien supprimé
avec le zip par les gabarits de bat modifiés par l'issue #105).

Release `v15` publiée et `master` poussé le 26/11/2026.
