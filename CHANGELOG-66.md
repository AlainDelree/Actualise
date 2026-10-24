# Changelog — issue #66

## Issue #66 — build_installe périmé après mise à jour par fenêtre, échec d'extraction fatal, ETAT.md obsolète

- **build_installe (point 1).** Le worktree reprenait un travail déjà
  entamé par une tentative précédente de cette même issue :
  `_generer_updater_bat` prenait déjà un paramètre `build` et le bat
  généré réécrivait déjà `build_installe` dans `config_actualise.json`
  via PowerShell, *après* la bascule effective de `Actualise.exe`/
  `_internal` et *avant* la suppression du zip source (évite le piège
  signalé dans l'issue : écrire le nouveau numéro trop tôt aurait fait
  voir le zip encore en attente comme un résidu obsolète et le
  supprimer). Écriture sans BOM (`UTF8Encoding($false)`), cohérente avec
  `config._ecrire_json_atomique`. **Mais le site d'appel dans
  `tache_verification_arriere_plan` n'avait pas été mis à jour** :
  `_generer_updater_bat` y était toujours appelé avec 3 arguments au
  lieu de 4, ce qui levait un `TypeError` à chaque mise à jour
  d'Actualise détectée — silencieusement avalé par le `except Exception`
  englobant de la tâche de fond, donc invisible dans les tests existants
  (le zip était déjà renommé en zone d'attente avant l'appel fautif, les
  assertions sur ce renommage passaient malgré tout). Corrigé en passant
  `build_distant` en 4ᵉ argument (`actualise.py`, dans
  `tache_verification_arriere_plan`). Solution restée localisée (un seul
  fichier, pas de nouveau processus ni de refonte du flux de bascule),
  conformément à la contrainte de l'issue.
- **Échec d'extraction non fatal pour l'application cible (point 2).**
  `mise_a_jour.extraire_zip`/`appliquer_manifeste` pour l'application
  cible n'étaient protégés contre aucune `OSError` dans
  `appliquer_mises_a_jour_en_attente` : une `PermissionError` (droits
  insuffisants en Program Files, ou fichier verrouillé parce que
  l'application — qui lance Actualise à son démarrage — tourne encore)
  remontait telle quelle et faisait planter Actualise (fenêtre Windows
  « Unhandled exception »). Entouré d'un `try/except OSError` : log
  `ERROR` explicite (cause probable, chemin concerné), zip conservé pour
  nouvelle tentative, `build_installe` non modifié, `continue` vers la
  cible suivante sans exception — même pattern déjà en place pour
  l'échec de renommage côté Actualise lui-même
  (`_basculer_par_renommage`).
  Vérification préalable (dossier inscriptible / exécutable principal
  non verrouillé) **évaluée mais non implémentée** : le cas réellement
  observé en octobre 2026 concernait un fichier verrouillé *dans une
  sous-arborescence* (`clr_loader\ffi\dlls\amd64\ClrLoader.dll`), pas
  l'exécutable principal — une vérification limitée au dossier racine
  ou à l'exécutable principal ne l'aurait pas détecté, et vérifier
  chaque fichier de l'archive avant extraction serait à la fois plus
  complexe et sujet à une course (TOCTOU) entre la vérification et
  l'extraction réelle. Le `try/except` protège déjà contre ce cas et
  tout autre, sans ce risque ni cette complexité.
- **Tests de non-régression.** Deux tests ajoutés dans
  `tests/test_actualise.py` :
  - `test_echec_extraction_application_cible_zip_conserve_aucune_exception`
    (classe `TestAppliquerMisesAJourEnAttente`) : simule une `PermissionError`
    lors de l'extraction, vérifie qu'aucune exception ne remonte, que le
    zip est conservé, que `build_installe` reste inchangé et qu'un log
    `ERROR` mentionnant l'extraction est émis.
  - `test_bat_updater_genere_avec_le_build_reellement_telecharge`
    (classe `TestTacheVerificationArrierePlan`) : vérifie que
    `_generer_updater_bat` est appelé avec le build réellement
    téléchargé comme dernier argument. Confirmé que ce test échoue sans
    le correctif du site d'appel (vérifié manuellement en reproduisant
    temporairement l'appel à 3 arguments).
  - Suite complète : 58 tests passent (`python3 -m pytest tests/`).
- **ETAT.md** mis à jour : Actualise v10 publié (Release contenant
  uniquement `actualise-v10.zip`, pas l'installeur), Scrabble v13 et
  Rummikub v13 publiés, rappel que les anciennes versions de Rummikub
  (v7 et antérieures, raccourci vers `Actualise.exe`) ne peuvent pas se
  mettre à jour seules vers la nouvelle architecture et exigent une
  installation manuelle du setup courant, rappel renforcé de la nécessité
  de supprimer `C:\Actualise\` avant réinstallation sur un ancien PC
  (`Actualise-Setup.exe` ne réécrit pas un `config_actualise.json`
  existant), et ajout du point ouvert sur la cause exacte (droits ou
  verrouillage) de l'échec d'extraction en Program Files, à trancher par
  un test en conditions réelles.
