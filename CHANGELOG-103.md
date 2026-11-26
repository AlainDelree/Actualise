# Changelog — issue #103

## Issue #103 (audit #117, SEC-025, SEC-024) — Garde anti-évasion pour le zip d'Actualise et noms d'entrées stricts pour le bat des jeux

Deux constats restants de l'audit #117, tous deux liés à l'extraction
des archives par PowerShell (`Expand-Archive`) dans les bat générés.

**SEC-025.** La branche « actualise » de `tache_verification_arriere_plan`
(tâche de vérification en arrière-plan) générait le bat + le flag de
mise à jour d'Actualise directement après téléchargement, sans passer
par la garde anti-évasion (`mise_a_jour.valider_entrees_zip`) déjà en
place pour la mise à jour d'un jeu et pour l'extraction Python directe
d'Actualise (`appliquer_mises_a_jour_en_attente`/`extraire_zip`). Un zip
contenant une entrée `../...` aurait été extrait tel quel par
`updater.bat`. Ajout de cette même validation avant génération du bat,
avec le même comportement de rejet que côté jeux : erreur journalisée,
zip et son fichier d'empreinte (`.sha256`) retirés, ni bat ni flag
écrits ; `BadZipFile` reste traité comme transitoire (zip conservé pour
une nouvelle tentative).

**Écart constaté et corrigé côté jeux (même SEC-025).** L'appel existant
dans `_assurer_maj_jeu_en_attente` validait les entrées contre
`repertoire_installation` (le dossier d'installation du jeu), alors que
`Expand-Archive` extrait réellement dans le sous-dossier
`repertoire_installation / "maj_bat"` (`EXTRACT_DIR` du gabarit, après
le `cd /d` vers ce dossier en tout début de script). Corrigé pour
valider contre ce dossier d'extraction réel — constat sans conséquence
pratique démontrée (la détection d'évasion par traversée relative donne
la même décision quel que soit le niveau de dossier choisi comme base),
mais corrigé pour correction et cohérence, l'intention de la garde étant
de valider contre l'endroit où l'extraction a réellement lieu. Même
correction appliquée à la nouvelle garde côté Actualise (validée contre
`config.chemin_config_portable() / "maj_bat"`).

**SEC-024.** Le bat d'un jeu écrit les noms d'entrées de premier niveau
de l'archive (`_lister_entrees_racine_zip`) directement dans des
commandes batch (`_bloc_bascule_entree_jeu`, `_bloc_annulation_entree_jeu`,
`_bloc_nettoyage_backup_jeu`), sans échappement — seul le nom de
l'application (`nom_app`) était déjà validé. Ajout de
`_entree_racine_jeu_valide` (`actualise.py`), appelée dans
`_assurer_maj_jeu_en_attente` avant génération du bat : liste blanche
prudente dans l'esprit de `_nom_jeu_valide`, mais qui accepte les noms
réels de premier niveau d'un zip de jeu (lettres y compris accentuées,
chiffres, espaces et points internes — ex. `Scrabble.exe`, `_internal`,
`data`, voir INTEGRATION.md « zip à plat »). Refuse : nom vide, `.` ou
`..` (ou en contenant), nom commençant/finissant par un espace ou un
point, tout caractère de contrôle, tout séparateur de chemin (`/`,
`\`), tout chemin absolu/lecteur (`:`), et les caractères spéciaux de
cmd.exe (`%`, `!`, `^`, `&`, `|`, `<`, `>`, `"`). Un nom refusé est
traité comme une évasion de chemin : même rejet fail-safe que SEC-025
(erreur journalisée, zip et empreinte retirés, ni bat ni flag écrits).

**Tests ajoutés** (`tests/test_actualise.py`) :
- `TestTacheVerificationArrierePlan.test_evasion_chemin_actualise_zip_rejete_sans_bat_ni_flag` :
  zip d'Actualise avec une entrée `../evasion.txt` → rejeté avant toute
  génération de bat/flag, zip et empreinte retirés, aucune notification
  ntfy trompeuse.
- `TestTacheVerificationArrierePlan.test_entree_jeu_caractere_special_cmd_rejetee_sans_bat_ni_flag` :
  zip de jeu avec une entrée `evil&name.exe` → même rejet côté jeu.
- `TestEntreeRacineJeuValide` : noms réels valides (accentués, points,
  espaces internes) et noms invalides (vide, `..`, caractères de
  contrôle, séparateurs, chemin absolu/lecteur, caractères spéciaux de
  cmd.exe, espace/point en tête ou en fin).
- Les tests déjà en place (dont les deux tests d'évasion de chemin
  existants, SEC-025 historique) passent inchangés.

**Documentation.** `docs/contexte/bascule_mise_a_jour.md` : section
« Garde anti-évasion de chemin » mise à jour pour décrire les trois
chemins désormais protégés (extraction Python directe, bat de jeu, bat
d'Actualise) et le dossier de validation réel (`maj_bat`) ; nouvelle
section « Noms d'entrées de premier niveau d'un zip de jeu » pour
SEC-024. `docs/contexte/maj_application_cible.md` : mention de la
validation des noms d'entrée avant génération du bat, avec renvoi vers
le domaine ci-dessus. `.audit.json` : aucune entrée existante ne
décrivait SEC-025/SEC-024 comme non traités, rien à y modifier.

Vérifications :
- `ruff check . --no-cache` (ruff 0.17.4, depuis la racine) →
  `All checks passed!`.
- `python3 -m pytest -q` → 92 tests passés + 10 ignorés sous Linux
  (gabarits de bat Windows), soit 102 au total (98 existants + 4
  nouveaux), aucun échec.
