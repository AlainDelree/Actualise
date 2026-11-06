# Changelog — issue #89

## Issue #89 — Audit #92 : le build Windows écrit la liste exacte des versions installées

- `build\rebuild_actualise.bat` (étape 3/9) : relevé de `pip freeze --all`
  dans l'environnement virtuel `.venv_build`, dans un seul fichier
  `versions-installees-v<N>.txt`, en deux temps : juste après
  `pip install -r requirements.txt` (dépendances d'exécution, avant
  PyInstaller — c'est ce qui sera épinglé) puis après
  `pip install pyinstaller` (environnement de build complet). En tête
  du fichier, la version de Python de cet environnement. Écrit dans
  tous les modes (avec ou sans `--publier`), copié dans
  `installeur\output` du worktree puis dans le dossier fixe
  `C:\CCW_Share\_derniers_builds\actualise\`, avant la suppression du
  dossier de build local — même traitement d'erreur (message clair +
  code de sortie 1) que les autres étapes du script.
- Aucun autre changement de comportement : mêmes arguments, mêmes
  refus, mêmes artefacts, rien d'écrit dans `version.json` sans
  `--publier`.
- But : préparer l'épinglage de `requirements.txt` (dépendances de
  `requests`, flottantes depuis l'issue #76) dans une issue séparée, à
  partir des versions réellement embarquées dans un build Windows réel.
