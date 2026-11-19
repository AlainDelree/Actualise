# Contexte — Projet Actualise

## Règles invariantes

- Actualise n'est jamais lancé directement par l'utilisateur final (ni
  raccourci, ni menu Démarrer) : c'est l'application cible qui le lance.
- L'application cible lance `Actualise.exe --config <nom>` à son propre
  démarrage, par un `Popen` non bloquant, sans attendre sa fin ni
  bloquer sa propre fenêtre.
- Actualise ne bloque jamais l'utilisateur et se termine dès que sa
  tâche de fond (vérification/téléchargement) est terminée — ce n'est
  pas un processus permanent.
- La comparaison de version se fait par un entier de build
  (`version.json`), jamais par chaîne semver ni comparaison de chaînes
  brute.
- Toute vérification réseau utilise un timeout court (2 à 3 secondes),
  avec repli silencieux sur la version installée en cas d'échec.
- Une seule instance d'Actualise, partagée entre toutes les applications
  cibles de la machine, avec un fichier de configuration séparé par
  application cible (`config_<nom>.json`).

## Architecture

- Exécutable séparé de l'application cible, plus `ActualiseUI.exe` pour
  le dialogue de mise à jour côté utilisateur final.
- GitHub Releases comme seul vecteur de distribution des binaires (un
  asset zip par tag, `version.json` commité à part).
- Mécanisme flag + bat comme bascule différée, pour contourner le verrou
  Windows sur un exécutable en cours d'exécution.

## Conventions de nommage

- Asset de Release : `<préfixe>-v<build>.zip` (ex. `actualise-v48.zip`,
  `scrabble-v48.zip`).
- Tag de Release : `v<build>` (ex. `v48`).
- Zip en zone d'attente : `<préfixe>_<build>.zip` (ex.
  `actualise_48.zip`).
- Bat de jeu : `updater_<nom>.bat`, écrit sous le dossier partagé
  d'Actualise.

## Index des fichiers de domaine

- `docs/contexte/vue_ensemble.md` — quand le lire : pour l'objectif
  général et le principe de fonctionnement (qui lance qui).
- `docs/contexte/versioning.md` — quand le lire : pour le format de
  `version.json`, la comparaison par build, le nommage des zips.
- `docs/contexte/distribution_releases.md` — quand le lire : pour la
  publication des binaires via GitHub Releases et le manifeste de mise
  à jour.
- `docs/contexte/configuration.md` — quand le lire : pour le contenu des
  fichiers `config_*.json` et la résolution du dossier de configuration
  portable.
- `docs/contexte/demarrage_reseau.md` — quand le lire : pour le timeout
  réseau et la séquence de démarrage non bloquante.
- `docs/contexte/bascule_mise_a_jour.md` — quand le lire : pour le
  garde-fou anti-boucle, la bascule sécurisée, les contrôles
  SHA-256/zip-slip.
- `docs/contexte/actualiseui_dialogue.md` — quand le lire : pour le
  dialogue `ActualiseUI.exe` de mise à jour d'Actualise lui-même.
- `docs/contexte/maj_application_cible.md` — quand le lire : pour la
  généralisation de la mise à jour à une application cible (jeu).
- `docs/contexte/integration_setup.md` — quand le lire : pour
  l'intégration avec le setup.exe d'une application cible.

Voir aussi `README.md` (structure du dépôt, lancement, tests) et
`INTEGRATION.md` (guide d'intégration d'une application cible).
