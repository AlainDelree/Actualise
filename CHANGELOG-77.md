# Changelog — issue #77

## Issue #77 — Audit #92 : aligne ETAT.md/TACHES.md/README sur le dépôt réel

- **ETAT.md** : la référence à `build\rebuild_actualise_unifie.bat`
  (issue #67) est remplacée par le nom réel `build\rebuild_actualise.bat`,
  avec note du renommage par l'issue #70 ; le point « en suspens »
  annonçant ce renommage et le retrait des trois anciens scripts
  (`rebuild_actualise.bat`, `rebuild_actualise_setup.bat`,
  `publier_actualise.bat`) comme une tâche future est retiré, ce travail
  ayant déjà été fait (issue #70, confirmé par l'état actuel du dépôt :
  seul `build\rebuild_actualise.bat` existe, `.gitignore`/`actualise.spec`/
  `installeur\actualise.iss` ne citent plus les anciens noms) ; la
  mention de `verifier_installation.py` est reformulée pour expliciter
  qu'il s'agit d'un script « hors dépôt » (sur le PC Windows d'Alain),
  sans retirer la référence.
- **TACHES.md** : retrait de la tâche de renommage/retrait de scripts,
  déjà accomplie (issue #70).
- **README.md** : réécriture complète — l'état « squelette initial,
  implémentation à venir » est remplacé par l'état réel (application
  complète et déployée) ; le « Principe général », qui décrivait encore
  un raccourci pointant vers Actualise lui-même, est corrigé pour
  refléter l'architecture actée depuis l'issue #73 (le raccourci pointe
  vers l'application cible, qui lance Actualise à son propre démarrage) ;
  ajout d'un renvoi vers INTEGRATION.md et d'une section « Lancement et
  build » citant `build\rebuild_actualise.bat --publier`.
- **Recherche dans tout le dépôt** (`grep`/`find`) : confirmé que
  `rebuild_actualise_unifie.bat`, `rebuild_actualise_setup.bat`,
  `publier_actualise.bat` et `verifier_installation.py` n'existent nulle
  part dans le dépôt, sous aucun nom. `.gitignore`, `actualise.spec` et
  `installeur\actualise.iss` ne citent déjà plus que le nom réel
  `rebuild_actualise.bat`.
- **CHANGELOG.md** : volontairement non modifié — c'est un journal
  historique, les anciens noms de scripts qu'il cite reflètent l'état du
  dépôt au moment de chaque issue passée, pas une erreur à corriger.
