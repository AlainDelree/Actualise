# Changelog — issue #109

## Issue #109 — Build Windows Actualise, version v16

Build de publication build 16 d'Actualise, à partir du commit 39778d9
(tête de master au moment du build, premier build contenant les issues
#107 et #108). `version.json` mis à jour (build 16, SHA-256 de l'archive
d2254a0e2a2d3a8821d5a6d333ecd09c6a700dab0f010fcde57c78eb88c411bc).
Aucun changement de code applicatif : build de release pur, numéro
imposé explicitement en ligne de commande (`--build 16`). Installeur
(20 696 158 octets) et archive (20 608 032 octets) produits et recopiés
par le script dans `C:\CCW_Share\_derniers_builds\actualise\` — écart
négligeable (quelques centaines d'octets) avec les tailles du build 15
publié (20 690 827 / 20 608 285 octets), sans cause identifiée autre que
la variabilité normale de compilation. Archive de 31 entrées vérifiée
(`Actualise.exe`, `ActualiseUI.exe`, `manifest.json` sans BOM UTF-8,
dossier `_internal`), `manifest.json` conforme
(`{"build": 16, "supprimer": []}`), `notes_de_version/v16.md` écrit et
commité séparément. Publication GitHub (Release, push) laissée à Alain.
