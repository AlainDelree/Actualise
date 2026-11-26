# Changelog — issue #105

## Issue #105 — Suites du build 14 : documentation « liste de refus », noms d'entrées ASCII, fin du faux message ntfy, nettoyage des .sha256

Quatre constats mineurs restants après la publication et la validation
sous Windows du build 14.

**1. Documentation « liste de refus ».** `_entree_racine_jeu_valide`
n'a jamais été une liste blanche : elle refuse une liste précise de cas
(nom vide/`.`/`..`, espace ou point en tête/fin, caractère de contrôle,
séparateur de chemin, `:`, caractères spéciaux de cmd.exe) et accepte
tout le reste. La documentation disait pourtant « liste blanche » à
plusieurs endroits — corrigé dans `docs/contexte/bascule_mise_a_jour.md`
(section « Noms d'entrées de premier niveau d'un zip de jeu », qui
énumère maintenant explicitement chaque catégorie refusée, note la
règle ASCII ci-dessous, et précise que les caractères `( ) , ; =` et les
noms de périphériques Windows (`nul`, `con`, `aux`…) restent acceptés
sans risque connu), `docs/contexte/maj_application_cible.md`,
`docs/contexte/demarrage_reseau.md` (nuance sur la notification ntfy,
voir point 3), la docstring et les commentaires de
`_entree_racine_jeu_valide`/`_CARACTERES_SPECIAUX_CMD` dans
`actualise.py`, et la formule de l'entrée #103 dans `CHANGELOG.md`
(correction de formulation minimale, sans réécrire l'historique).

**2. Noms d'entrées ASCII.** `_entree_racine_jeu_valide` refuse
désormais tout nom d'entrée de premier niveau contenant un caractère
non ASCII (`nom_entree.isascii()`), en plus des refus déjà en place —
même traitement que les autres rejets (erreur journalisée, zip et
empreinte retirés, ni bat ni flag écrits). Motif : le bat généré est
écrit en UTF-8 sans changement de page de code (`chcp`), un nom accentué
y serait mal lu par cmd, la bascule échouerait puis serait annulée,
silencieusement pour l'utilisateur (seulement dans le journal). Les 35
noms réels de premier niveau du zip Scrabble v15 restent tous acceptés
(tous ASCII, dont des noms à tiret comme `libssl-3.dll`) — gardés comme
cas de test. `INTEGRATION.md` (§5, « Format des Releases GitHub de
l'application cible ») reçoit une phrase à l'intention des constructeurs
de jeux : les noms de premier niveau du zip doivent être en ASCII, un
nom accentué serait rejeté à chaque lancement sans message visible pour
l'utilisateur final. `docs/contexte/integration_setup.md` ne reprend pas
ce sujet (setup.exe uniquement) : rien à y changer.

**3. Fin du faux message ntfy.** `_assurer_maj_jeu_en_attente` retourne
désormais un booléen : `False` uniquement pour les trois rejets qui
laissent le zip sans bat/flag régénérable (nom d'application invalide,
évasion de chemin, nom d'entrée de premier niveau invalide — y compris
le nouveau cas non ASCII du point 2) ; `True` dans tous les autres cas.
`tache_verification_arriere_plan` saute la notification ntfy « Mise à
jour disponible… elle sera appliquée au prochain lancement » quand cette
valeur est `False`, puisque le zip vient d'être retiré et que le message
serait faux. Cas **couverts** (plus de notification) : nom d'application
cible invalide, évasion de chemin détectée dans le zip du jeu, nom
d'entrée de premier niveau invalide (dont non ASCII). Cas **laissés tels
quels** (notification toujours envoyée) : « un flag est déjà en attente »
(mise à jour simplement reportée, toujours valide) ; échecs transitoires
qui conservent le zip pour nouvelle tentative (`OSError`/`BadZipFile` à
la lecture des entrées, échec de génération du bat, échec d'écriture du
flag). La branche Actualise elle-même n'était pas concernée : son rejet
passait déjà par un `continue` qui sautait la notification.

**4. Nettoyage des `.sha256` orphelins.** Nouvelle fonction
`_nettoyer_empreintes_orphelines(zone_attente)`, appelée en tout début
de `appliquer_mises_a_jour_en_attente` (étape 4, à chaque démarrage) :
supprime tout fichier `*.zip.sha256` de la zone d'attente dont le zip
correspondant n'existe plus, sans jamais toucher à l'empreinte d'un zip
encore présent — couvre à la fois les résidus déjà présents (constatés
le 26/11 : `actualise_14.zip.sha256`, `scrabble_15.zip.sha256`) et les
nouveaux cas. En complément, les deux gabarits de bat
(`_GABARIT_UPDATER_BAT` et `_GABARIT_UPDATER_BAT_JEU`) suppriment
désormais `%ZIP%.sha256` juste après `%ZIP%` à la fin d'une bascule
réussie, pour ne plus créer de nouvel orphelin — sans changer le
déroulement ni la sécurité de la bascule (aucune autre ligne modifiée).
Nettoyage fait côté Python (point d'entrée unique, couvre aussi les
résidus déjà présents) **et** côté bat (ceinture et bretelles pour les
nouveaux cas).

**Tests ajoutés/modifiés** (`tests/test_actualise.py`) :
- `TestEntreeRacineJeuValide.test_noms_reels_scrabble_v15_acceptes` :
  les 35 noms réels de premier niveau du zip Scrabble v15 (représentatifs
  — le dépôt Scrabble est hors périmètre de ce dépôt — reconstitués à
  partir de la structure PyInstaller `--onedir` documentée) restent
  acceptés.
- `TestEntreeRacineJeuValide.test_noms_invalides` : étendu avec des noms
  non ASCII (accents, japonais) désormais refusés.
- `TestEntreeRacineJeuValide.test_noms_reels_valides` : les deux noms
  accentués fictifs retirés (plus acceptés), remplacés par un cas ASCII
  couvrant `( ) , ; =`.
- `TestTacheVerificationArrierePlan.test_entree_jeu_caractere_special_cmd_rejetee_sans_bat_ni_flag` :
  capture désormais `notifications` et vérifie `notifier_ntfy.assert_not_called()`
  (absent avant cette issue — le test ne couvrait pas le faux message).
- `TestTacheVerificationArrierePlan.test_nom_entree_non_ascii_rejetee_sans_bat_ni_flag_ni_notification` :
  nouveau, nom d'entrée accentué → zip et empreinte retirés, aucune
  notification.
- `TestTacheVerificationArrierePlan.test_jeu_zip_accepte_notification_toujours_envoyee` :
  nouveau, non-régression — un zip de jeu accepté continue de notifier.
- `TestAppliquerMisesAJourEnAttente.test_empreinte_orpheline_supprimee_empreinte_zip_present_conservee` :
  nouveau, nettoyage au démarrage via `appliquer_mises_a_jour_en_attente`.
- `TestNettoyerEmpreintesOrphelines` (nouvelle classe, 3 tests) : la
  fonction `_nettoyer_empreintes_orphelines` testée directement (zip
  absent → empreinte supprimée ; zip présent → empreinte conservée ;
  zone d'attente inexistante → aucune exception).

Suite complète : 99 tests passent (92 avant cette issue + 7 nouveaux),
10 tests Windows ignorés sous Linux comme d'habitude — aucune
régression. `ruff check --no-cache .` : « All checks passed! ». Aucun
`# noqa`/`# nosec` ajouté ou modifié ; gabarits de bat touchés
uniquement pour la ligne `del /f "%ZIP%.sha256" 2>nul` du point 4 ;
`configs/*.conf` non touché ; `actualise.py` non découpé (ARC-004,
toujours reporté).

**Documentation.** `docs/contexte/` mis à jour pour les quatre points :
`bascule_mise_a_jour.md` (liste de refus complète, règle ASCII,
nettoyage des sidecars orphelins), `maj_application_cible.md` (liste de
refus, suppression de la notification ntfy sur rejet),
`demarrage_reseau.md` (nuance sur la notification ntfy pour un rejet de
jeu). `CONTEXTE.md` inchangé : aucune règle ni convention invariante ne
change dans cette issue.
