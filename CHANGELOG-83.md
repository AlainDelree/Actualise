# Changelog — issue #83

- Correction (suite #82) : le marqueur `lent` est désormais facultatif.
  `tests/test_actualise.py` ne dépend plus de `pytest` (retrait de
  `import pytest` et des deux décorateurs `@pytest.mark.lent`
  directement sur `TestGabaritUpdaterBat` et `TestGabaritUpdaterBatJeu`) :
  `python3 -m unittest discover -s tests` reste exécutable sans `pytest`
  installé. Le marqueur est posé à la place par un nouveau
  `tests/conftest.py` (lu uniquement par `pytest`, ignoré par
  `unittest discover`), via `pytest_collection_modifyitems`. `pytest.ini`
  (déclaration du marqueur) est inchangé.
- Documentation (`README.md`, section Tests) : la commande principale
  redevient `python3 -m unittest discover -s tests` ; `pytest` et
  `pytest -m "not lent"` sont mentionnés comme options facultatives
  supposant `pytest` installé (absent de `requirements.txt`).
- Vérifications effectuées : `python3 -m unittest discover -s tests`
  (86 tests, 10 ignorés, OK) rejoué à l'identique avec l'import de
  `pytest` rendu impossible en simulation (même résultat : 86 tests,
  10 ignorés, 0 erreur) ; `pytest -m "not lent"` désélectionne bien les
  10 tests lents (76 passed, 10 deselected) ; `pytest` complet passe
  (76 passed, 10 skipped — tests Windows ignorés sous Linux).
- Hors périmètre, non traité : les 14 autres violations du linter de
  l'outil d'audit relevées par #82 (aucun linter n'est en réalité
  configuré dans le dépôt — seul `pyflakes` a pu être utilisé pour #82,
  avec 1 violation corrigée) ; aucun reformatage du code de mise à jour
  (`actualise.py`, `mise_a_jour.py`, `config.py`, `notifications.py`,
  `version_check.py`, `actualise_ui.py`).
