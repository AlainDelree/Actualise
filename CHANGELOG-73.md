# Changelog — issue #73

## Issue #73 — Applique la mise à jour d'un jeu à sa fermeture, avec le mécanisme flag + updater.bat

- **Cause corrigée** (diagnostic issue #72) : l'application cible lance
  `Actualise.exe --config <nom>` par un `Popen` non bloquant à son
  propre démarrage et continue de tourner sans l'attendre — son
  exécutable est donc, en usage normal, **toujours** en cours
  d'exécution au moment où Actualise voulait appliquer sa mise à jour.
  L'extraction directe (`extractall`) échouait alors silencieusement
  (fichiers verrouillés), le zip restant indéfiniment en zone d'attente,
  retéléchargé à chaque lancement sans jamais s'appliquer.
- **Généralisation du mécanisme flag + bat**, jusqu'ici réservé à la
  mise à jour d'Actualise lui-même (issue #36/#68), à la mise à jour
  d'une application cible :
  - `_lister_entrees_racine_zip` inspecte le zip téléchargé et liste ses
    entrées de premier niveau (fichiers/dossiers) ;
  - `_generer_updater_bat_jeu` génère un bat dédié au jeu (dans son
    propre dossier d'installation), avec un bloc de bascule
    renommage+déplacement par entrée (jamais de déplacement direct vers
    un nom encore existant), restauration complète de l'état initial au
    moindre échec, attente réelle de la fin du jeu **et** de
    `Actualise.exe`/`ActualiseUI.exe` (limite de temps, abandon sans
    rien modifier au-delà), journal `updater.log`, et réécriture de
    `build_installe` dans `config_<nom>.json` (sans BOM) seulement après
    bascule confirmée ;
  - `_ecrire_flag_maj` accepte désormais un champ `type_maj`
    (`"actualise"` ou `"jeu"`), ajouté au JSON du flag — facultatif,
    ignoré par le code déjà déployé dans les jeux (seul le nom de
    fichier `actualise_update.flag` compte pour eux) ;
  - `_assurer_maj_jeu_en_attente` orchestre la génération (appelée au
    téléchargement dans `tache_verification_arriere_plan`, et en retry
    au lancement suivant depuis `appliquer_mises_a_jour_en_attente`) ;
    ne fait rien si un flag est déjà présent dans le dossier du jeu — un
    seul type de mise à jour en attente à la fois, celle d'Actualise
    passant toujours en premier (ordre de traitement des cibles).
- **Suppression de l'extraction directe d'un jeu** dans
  `appliquer_mises_a_jour_en_attente` : un zip de jeu ne s'applique plus
  que via ce bat. Si le bat/flag ne peut pas être généré (`OSError`,
  zip invalide), le zip est conservé et l'échec journalisé, sans aucune
  extraction.
- **Non traité par le bat du jeu** : `manifest["supprimer"]` (limitation
  connue et documentée, non demandée par l'issue, risque jugé non
  proportionné pour un gain non démontré) ; application directe sans
  attendre une fermeture du jeu quand Actualise est lancé à la main
  alors que le jeu ne tourne pas (facultatif, non traité — voir rapport
  de clôture de l'issue).
- **Documentation** : CONCEPTION.md corrigé (le raccourci pointe vers le
  jeu, pas vers Actualise ; l'exécutable du jeu tourne bien pendant la
  bascule) et complété (généralisation du mécanisme flag + bat, cas
  limite du flag survivant jusqu'au démarrage suivant du jeu) ;
  INTEGRATION.md complété avec le lancement d'Actualise par le jeu
  (jusqu'ici non documenté) et les deux usages du flag.
- **Tests** : `tests/test_actualise.py` — nouveaux tests de décision
  (flag généré avec le bon contenu pour un jeu, jamais d'extraction
  directe, aucun nouveau flag tant qu'un flag existe, priorité
  d'Actualise sur un jeu au même cycle) et nouvelle classe
  `TestGabaritUpdaterBatJeu` (exécution réelle du bat généré : succès,
  jeu encore ouvert à l'échéance, fichier verrouillé, zip invalide —
  mêmes scénarios que `TestGabaritUpdaterBat`, issue #68, appliqués au
  cas générique d'un jeu).
