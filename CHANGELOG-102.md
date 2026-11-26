# Changelog — issue #102

## Issue #102 (audit #117, SEC-003) — Remplacer les deux `# noqa: S603` par `# nosec B603`

Avec `ruff check --no-cache .` sans configuration, S603 n'est pas actif :
les deux directives `# noqa: S603` posées par l'issue #101 sont vues comme
« noqa inutile » (RUF100, 2 erreurs, ruff 0.17.3 et 0.17.4). L'outil
d'audit (Diagnostique_Programme) reconnaît la directive bandit
`# nosec B603` sur la ligne de l'appel, avec la raison dans le bloc de
commentaires contigu au-dessus. Remplacement des deux directives, sans
toucher aux blocs de justification ni au code.

- `actualise.py`, ligne 153 (`_relancer_en_enfant`) : `# noqa: S603` →
  `# nosec B603`.
- `actualise_ui.py`, ligne 85 (`mettre_a_jour`) : `# noqa: S603` →
  `# nosec B603`.

Vérifications :
- `~/Diagnostique_Programme/.venv_outils/bin/ruff check --no-cache .`
  (ruff 0.17.3) → `All checks passed!` (plus de RUF100).
- `ruff check --no-cache --select S603,S607 .` : avant (avec
  `# noqa: S603`) → 13 erreurs, les deux lignes ciblées absentes (noqa
  natif à ruff, donc supprimé par ruff lui-même) ; après (avec
  `# nosec B603`) → 15 erreurs, les deux lignes ciblées réapparaissent en
  S603 seul (ruff n'interprète pas `# nosec` : résultat attendu, signalé
  pour information, pas corrigé). Aucun S607 sur ces deux lignes.
- `git grep -n -E "noqa|nosec" -- actualise.py actualise_ui.py` : seules
  les deux directives `# nosec B603` apparaissent.
