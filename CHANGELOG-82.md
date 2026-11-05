# Changelog — issue #82

## Issue #82 — Audit #92 : violations du linter et isolation des tests lents

- **PRO-001** : seul linter réellement disponible dans l'environnement
  d'exécution (aucun `.flake8`/`pyproject.toml`/`.pylintrc` n'est
  configuré dans le dépôt) : `pyflakes`. Il relevait une seule
  violation réelle — `shutil` importé sans usage dans
  `tests/test_mise_a_jour.py` — supprimée. Le chiffre de 15 violations
  de l'audit #92 n'a pas pu être reproduit faute d'un linter plus
  complet (ruff/flake8/pylint) disponible ici ; voir le rapport de
  clôture de l'issue #82 pour le détail.
- **TST-003** : nouveau marqueur pytest `lent` (déclaré dans
  `pytest.ini`), appliqué à `TestGabaritUpdaterBat` et
  `TestGabaritUpdaterBatJeu` (`tests/test_actualise.py`) — ces classes
  exécutent réellement `updater.bat` via `subprocess` avec plusieurs
  attentes de plusieurs secondes (`time.sleep`, `Start-Sleep`, `ping`),
  actives uniquement sous Windows mais lentes quand elles tournent.
  Commande d'exécution rapide documentée dans le README :
  `pytest -m "not lent"`.
