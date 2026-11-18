# Changelog — issue #92

## Issue #92 — Build Windows Actualise, version v13 (publication)

- Build de publication exécuté via `build\rebuild_actualise.bat --publier
  --build 13`, sur le commit dbc196d (contient #84, #89, #90).
- `version.json` : build 13, SHA-256 de `actualise-v13.zip` recalculé et
  vérifié identique à celui écrit par le script.
- Artefacts produits dans `installeur\output\` et copiés vers
  `C:\CCW_Share\_derniers_builds\actualise\` : `Actualise-Setup-v13.exe`
  (20 655 924 octets), `actualise-v13.zip` (20 586 096 octets),
  `versions-installees-v13.txt`.
- `manifest.json` de l'archive : `{"build": 13, "supprimer": []}`, sans
  BOM (premiers octets `7B 22 62`).
- `versions-installees-v13.txt` : certifi 2026.10.23,
  charset-normalizer 3.5.2, idna 3.20, requests 2.34.2, urllib3 2.8.0 —
  conforme.
- Aucun `git push` ni `gh release create` : étapes manuelles restantes
  pour Alain (fusion vers master, création de la Release v13 avec les
  deux fichiers, push).
