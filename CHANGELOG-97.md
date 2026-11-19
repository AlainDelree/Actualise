# Changelog — issue #97

## Issue #97 — Corriger les renvois à CONTEXTE.md après le découpage en fichiers de domaine

Suite à l'issue #96 (découpage de `CONTEXTE.md` en 9 fichiers sous
`docs/contexte/`), tous les renvois « voir CONTEXTE.md, section X »
citaient des sections qui n'existent plus à cet endroit. Correction de
~45 renvois dans 15 fichiers, sans aucun changement de comportement
(commentaires/docstrings/documents uniquement).

- `actualise.py` : tous les renvois `CONTEXTE.md` corrigés vers le
  fichier de domaine contenant désormais la section citée —
  `docs/contexte/demarrage_reseau.md` (« Séquence de démarrage »,
  « Cycle de vie du processus Actualise »), `docs/contexte/bascule_mise_a_jour.md`
  (« Garde-fou anti-boucle infinie »), `docs/contexte/versioning.md`
  (« Nommage versionné des zips en zone d'attente », cas limite
  plusieurs zips), `docs/contexte/distribution_releases.md`
  (« Distribution des binaires », « Manifeste de mise à jour »),
  `docs/contexte/actualiseui_dialogue.md` et
  `docs/contexte/maj_application_cible.md` (mécanisme flag+bat,
  généralisation à une application cible). Un seul renvoi laissé sur
  `CONTEXTE.md` seul (`--noconsole`/architecture, `configurer_logging`,
  ligne 1381) : aucun fichier de domaine ne documente ce choix
  d'empaquetage, qui reste dans la section « Architecture » de
  `CONTEXTE.md` lui-même.
- `config.py` : renvois vers `docs/contexte/configuration.md`. Nom de
  section périmé « Contenu de config.json » remplacé par le titre
  actuel, « Contenu des fichiers de configuration —
  `config_actualise.json` / `config_<nom_app>.json` ».
- `mise_a_jour.py` : renvois répartis vers
  `docs/contexte/distribution_releases.md`,
  `docs/contexte/demarrage_reseau.md` et `docs/contexte/versioning.md` ;
  l'ancien renvoi à « Vérification SHA-256 du zip » dans le tableau
  disparu « Décisions actées » pointe maintenant vers
  `docs/contexte/bascule_mise_a_jour.md`, « Vérification SHA-256 à
  l'application (sidecar, SEC-022) ».
- `version_check.py` : renvois vers `docs/contexte/versioning.md`
  (« Format de version », « Deux fichiers `version.json` distincts »,
  piège lexicographique) et `docs/contexte/demarrage_reseau.md`
  (« Vérification réseau — timeout strict », qui couvre aussi l'ancien
  renvoi « Décisions actées » sur le repli silencieux).
- `notifications.py` : renvoi « Contenu de config.json » remplacé par
  `docs/contexte/configuration.md` (nom de section à jour) ; l'ancien
  renvoi « Décisions actées » (repli silencieux sur échec réseau)
  remplacé par `docs/contexte/demarrage_reseau.md`, « Vérification
  réseau — timeout strict ».
- `actualise.spec` et `.audit.json` : renvoi générique `--noconsole`
  précisé (« CONTEXTE.md, architecture ») ; `.audit.json` seul le texte
  de la justification SEC-022 modifié, pour pointer vers
  `docs/contexte/bascule_mise_a_jour.md` — aucune autre clé/valeur
  touchée.
- `INTEGRATION.md` : phrase d'accroche complétée pour citer aussi
  l'index `docs/contexte/` ; renvoi « Séquence de démarrage » vers
  `docs/contexte/demarrage_reseau.md` ; renvoi « ActualiseUI.exe, cas
  limite dédié » (flag survivant à une extinction PC) corrigé vers
  `docs/contexte/maj_application_cible.md`, « Cas limite : le flag
  survit jusqu'au démarrage suivant du jeu » (section réellement
  concernée).
- `README.md` : phrase d'accroche adaptée pour citer l'index de
  `CONTEXTE.md` et le dossier `docs/contexte/` plutôt que l'ancien
  « rapport de conception complet » (devenu inexact depuis le
  découpage).
- Tests (`tests/test_actualise.py`, `tests/test_config.py`,
  `tests/test_version_check.py`, `tests/test_notifications.py`,
  `tests/test_mise_a_jour.py`) : mêmes corrections de renvois que les
  modules qu'ils testent.
- `ETAT.md` : suppression de la ligne périmée « Fiabilisation de
  updater.bat à prévoir (issue pas encore créée) » dans « Points en
  suspens » — vérifié que l'issue #68 (« updater.bat fiabilisé : attente
  réelle, contrôle de chaque étape, journal, ActualiseUI.exe basculé »,
  voir `CHANGELOG.md`) a bien traité ce point (attente réelle des
  processus, contrôle de chaque étape, `ActualiseUI.exe` désormais
  basculé, journal `updater.log`), confirmé par le docstring actuel de
  `_generer_updater_bat` dans `actualise.py`. Aucune autre ligne
  d'`ETAT.md` modifiée.

Renvois volontairement laissés sur `CONTEXTE.md` seul (aucune section de
domaine ne couvre le point cité, c'est l'architecture générale de
l'index qui est visée) :
- `actualise.py:1381` (`configurer_logging`) et `actualise.spec`
  (×3, dont le commentaire inline `console=False`) : choix
  d'empaquetage `--noconsole`, documenté uniquement dans la section
  « Architecture » de `CONTEXTE.md`.
- `tests/test_actualise.py` (`TestMain`) : même raison (``--noconsole``).
- `INTEGRATION.md`, §1 et `README.md` : renvois à l'index lui-même
  (CONTEXTE.md comme point d'entrée vers `docs/contexte/`), désormais
  complétés pour le dire explicitement.

## Vérification
- Ruff 0.17.3 (`/home/alain/Diagnostique_Programme/.venv_outils/bin/ruff
  check . --no-cache`) : AVANT et APRÈS, « All checks passed! » (0
  erreur, aucun RUF100).
- Suite de tests (`python3 -m unittest discover -s tests`) : AVANT et
  APRÈS, 98 tests, `OK (skipped=10)` — résultats identiques.
- `git grep` final des renvois (hors `CHANGELOG*.md`) : plus aucune
  citation d'une section absente du fichier cité ; seuls les renvois
  listés ci-dessus restent volontairement sur `CONTEXTE.md` seul.
