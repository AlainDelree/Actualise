## Issue #63 — Toujours recopier les artefacts de build vers un chemin fixe sur le partage

- `build\rebuild_actualise_setup.bat` (étape [8/8]) : en plus de la copie
  existante vers `%ORIGDIR%\installeur\output\` (dépendante du worktree
  d'où le script est lancé), ajoute une seconde copie systématique de
  `Actualise-Setup-v<N>.exe` vers un chemin fixe et prévisible sur le
  partage : `C:\CCW_Share\_derniers_builds\actualise\`. Ce chemin est
  identique quel que soit le worktree d'origine — plus besoin de
  chercher sur le partage où l'installeur a atterri. Écrase sans
  confirmation le fichier déjà présent (comportement voulu : toujours le
  dernier artefact produit). Le comportement existant (copie vers
  `ORIGDIR`) est conservé tel quel. Documenté en tête de fichier
  (commentaire de l'étape 1).
- Testé avec un build factice, entièrement en bac à sable à l'intérieur
  du worktree (dossiers `origdir`/`fixedshare` simulant `ORIGDIR` et le
  chemin fixe) : les deux copies aboutissent, le chemin fixe est créé
  automatiquement par `robocopy` s'il n'existe pas encore, et une
  seconde exécution avec un contenu différent écrase silencieusement le
  fichier précédent au chemin fixe — confirmant qu'il contient toujours
  le dernier artefact produit.
- `build\publier_actualise.bat` (demandé par l'issue #62) **non
  modifié** : ce fichier n'existe pas encore sur la branche
  `worktree-issue-63` (issue #62 n'est pas encore mergée dans `master`,
  il vit uniquement sur `worktree-issue-62`). Fusionner du contenu
  d'une autre branche non mergée dans ce worktree sortait du périmètre
  de cette tâche. À traiter séparément, soit en appliquant le même
  correctif sur `worktree-issue-62` avant sa fusion, soit via une
  nouvelle issue une fois `publier_actualise.bat` présent sur `master`.
