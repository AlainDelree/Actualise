# Changelog — issue #70

## Issue #70 — Renomme le script de build unifié en rebuild_actualise.bat et retire les anciens scripts

- **Renommage** : `build\rebuild_actualise_unifie.bat` (issue #67) devient
  `build\rebuild_actualise.bat`. L'ancien `rebuild_actualise.bat` (build
  d'`Actualise.exe` seul, sans installeur ni archive) est supprimé
  d'abord. En-tête et messages d'aide réécrits pour décrire le script tel
  qu'il est, sans « provisoire » ni mention des anciens scripts.
- **Suppression** de `build\rebuild_actualise_setup.bat` et de
  `build\publier_actualise.bat` (leurs fonctions sont couvertes par le
  script unique depuis l'issue #67).
- **Références nettoyées** : `.gitignore` (note sur `git add -f`,
  réduite à l'unique script restant), `installeur\actualise.iss`
  (commentaire de compilation, mention VM/VirtualBox/VBOXSVR remplacée
  par une description du staging local). `actualise.spec` citait déjà le
  nom définitif, aucun changement nécessaire.
- **Essai réalisé** sans `--publier`, avec `--build 99` (numéro fictif,
  jamais utilisé en publication) : installeur et archive construits avec
  succès, copiés dans `installeur\output\` du worktree et dans
  `C:\CCW_Share\_derniers_builds\actualise\` ; structure de l'archive
  identique à la Release v11 (31 entrées, 4 éléments à la racine) ;
  `version.json` inchangé (vérifié par `git diff` vide).
- **Fonctions des anciens scripts non reprises dans le script unique**
  (signalées, non corrigées dans cette issue) : construction d'
  `Actualise.exe` seul avec recopie de `dist\` (ancien
  `rebuild_actualise.bat`), recopie de `dist\Actualise` et
  `dist\ActualiseUI.exe` vers le worktree (ancien
  `rebuild_actualise_setup.bat`), et refus d'un numéro de build
  inférieur ou égal à celui de `version.json` lors de la publication
  (ancien `publier_actualise.bat`).

Fichiers de test (build 99) laissés dans
`C:\CCW_Share\_derniers_builds\actualise\` : à supprimer à la main par
Alain, hors du périmètre de l'agent.
