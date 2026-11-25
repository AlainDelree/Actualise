# Changelog — issue #101

## Issue #101 (audit #117, SEC-003) — Justifier les deux constats S603 en ligne

Les deux appels `subprocess.Popen(commande)` signalés par l'audit #117
(règle SEC-003 : aucun motif dangereux d'analyse statique sans
justification) reçoivent chacun une directive `# noqa: S603` précédée
d'un bloc de commentaires expliquant pourquoi l'appel est sûr. Aucun
changement de code ni de logique : uniquement des commentaires et les
deux directives.

- `actualise.py`, lignes 146-153 (`_relancer_en_enfant`) : la ligne
  `subprocess.Popen(commande)` (désormais ligne 153) porte
  `# noqa: S603`. Le bloc de commentaire précise que `commande` est une
  liste d'arguments (jamais `shell=True`), composée de l'interpréteur ou
  de l'exécutable gelé, du chemin du script résolu si non gelé, de
  `--child`, puis de `--config` avec `nom_app` comme élément unique de
  liste — et précise que `nom_app` (reçu via l'argument `--config`)
  n'est pas validé à ce point (vérifié dans le code : la validation
  `_nom_jeu_valide` ne s'applique qu'au chemin « bat de jeu », pas à ce
  chemin de relance d'Actualise sur lui-même).
- `actualise_ui.py`, lignes 81-85 (`mettre_a_jour`) : la ligne
  `subprocess.Popen(commande)` (désormais ligne 85) porte
  `# noqa: S603`. Le bloc de commentaire précise que `commande` est une
  chaîne `cmd /c "..."` construite par `construire_commande_maj`, dont
  la partie interne est quotée par `subprocess.list2cmdline` à partir du
  chemin du bat (`--bat`) et, si présent, de `--relancer`, et que
  `shell=True` n'est pas utilisé.

Aucun S607 signalé sur ces deux lignes (vérifié avec
`ruff check --select S603,S607` avant modification) : chaque directive
ne porte donc que `S603`.

**Constat annexe (hors périmètre de cette tâche, signalé pour Alain)** :
ce dépôt n'a aucun fichier de configuration ruff (`pyproject.toml`,
`ruff.toml`...), donc le jeu de règles par défaut de `ruff check .` (sans
`--select`) n'active pas `S603`/`S607`. Résultat : les deux nouvelles
directives `# noqa: S603`, bien qu'indispensables pour l'outil d'audit
(qui sélectionne explicitement `S603,S607`), font apparaître 2 erreurs
`RUF100` (« unused noqa, non-enabled ») sous la commande nue
`ruff check --no-cache .`, alors qu'elles n'apparaissaient pas avant
cette tâche. Lever ce point nécessiterait un changement de configuration
ruff à l'échelle du dépôt (ex. `external = ["S603", "S607"]`), hors du
périmètre strict de cette issue (deux lignes, aucune autre modifiée) —
laissé à la décision d'Alain, éventuellement via une issue séparée.
