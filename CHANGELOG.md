# Changelog — issue #57

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

## Issue #62 — Implémenter build\publier_actualise.bat selon le plan diagnostiqué

- `build\rebuild_actualise_setup.bat` (étape [8/8]) : recopie désormais
  aussi `dist\Actualise\` (`/MIR`) et `dist\ActualiseUI.exe` vers le
  partage, en plus du setup compilé — `dist\` reste disponible après le
  build pour `publier_actualise.bat`, sans jamais réinstaller le setup.
- `build\publier_actualise.bat` (nouveau) : construit
  `installeur\output\actualise-v<N>.zip` et son `manifest.json` à partir
  de `dist\` (staging jetable `build\_staging_publication\`), affiche le
  SHA-256 en minuscules prêt à copier dans `version.json`, et rappelle
  explicitement les 2 étapes qui restent manuelles (`version.json` +
  `git push`, `gh release create`). Vérifications préalables : paramètre
  `%1` numérique obligatoire, `%1` strictement supérieur au build déjà
  publié, présence des 3 artefacts `dist\` attendus.
- Testé de bout en bout avec un `dist\` factice (build 11) : zip
  contenant exactement les 3 éléments + `manifest.json` (pas de dossier
  imbriqué), SHA-256 affiché vérifié indépendamment via `Get-FileHash`,
  et les 4 cas d'échec (paramètre absent, non numérique, build ≤
  publié, `dist\` absent) échouent proprement sans zip partiel.

# Changelog — issue #61

- Documentation (`CONCEPTION.md`, sections « Distribution des binaires —
  GitHub Releases » et « Décisions actées ») : correction du nommage
  d'asset documenté, qui décrivait un nom fixe sans numéro de version
  (`<préfixe>.zip`, réécrasé à chaque Release) alors que le code
  (`actualise.py::_url_asset_release`) construit et a toujours construit
  un nom versionné `<préfixe>-v<build>.zip` (ex. `actualise-v48.zip`,
  cohérent avec `_GABARIT_URL_RELEASE`). La documentation reflète
  désormais le comportement réel du code, avec l'explication du choix :
  cohérence avec le nommage déjà utilisé pour les applications cibles
  (ex. `Scrabble-Setup-v10.exe`), pas de dépendance à une URL « latest »
  puisque la publication reste pilotée manuellement par Alain. Aucun
  changement de code.

- Correction (`actualise.py`, `appliquer_mises_a_jour_en_attente`) : lecture
  de `manifest.json` extrait du zip en zone d'attente désormais décodée en
  `utf-8-sig` au lieu de `utf-8` strict, pour tolérer un BOM UTF-8 (InnoSetup
  peut écrire du JSON avec BOM, cf. issue #46 pour `config.py`). Corrige un
  crash au démarrage (`JSONDecodeError: Unexpected UTF-8 BOM`) confirmé en
  conditions réelles.
- Ajout d'un test de non-régression dans `tests/test_actualise.py`
  (`test_manifest_avec_bom_utf8_est_lu_correctement`), sur le modèle du test
  équivalent de `tests/test_config.py` pour l'issue #46.

