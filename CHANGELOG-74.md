# Changelog — issue #74

## Issue #74 — Construit le build 12 d'Actualise avec rebuild_actualise.bat --publier

- Build 12 construit via `build\rebuild_actualise.bat --publier` (numéro
  automatique, sans `--build`) : embarque les changements internes déjà
  sur `master` depuis le build 11 (updater.bat fiabilisé — issue #68,
  script de build unique avec garde-fou — issues #67/#70/#71, mise à jour
  d'un jeu appliquée à sa fermeture — issue #73).
- `version.json` mis à jour (build 12, SHA-256 de `actualise-v12.zip`) et
  commité localement par le script.
- `Actualise-Setup-v12.exe` et `actualise-v12.zip` produits dans
  `installeur\output` (non suivis par git, comme v11) et copiés par le
  script vers le dossier fixe du partage.
- Aucune Release créée, aucun push : étapes manuelles laissées à Alain.
