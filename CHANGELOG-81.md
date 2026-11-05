## Issue #81 — Audit #92 : actualise_ui.py, guillemets de `cmd /c` avec chemins contenant des espaces

- `construire_commande_maj` retourne désormais une chaîne unique (et non
  plus une liste) : `cmd /c "<partie interne quotée par list2cmdline>"`.
  Reproduit le comportement de l'ancien `shell=True` (qui entourait toute
  la ligne d'une paire de guillemets supplémentaire) sans le réintroduire,
  et corrige le cas où le chemin du bat ET celui de l'exécutable à
  relancer contiennent chacun un espace (`C:\Program Files\...`).
- `mettre_a_jour` passe cette chaîne telle quelle à `subprocess.Popen`
  (toujours sans `shell=True`).
- Tests remplacés dans `tests/test_actualise_ui.py` pour vérifier la
  chaîne produite (sans espace, bat seul avec espace, exécutable seul
  avec espace, les deux à la fois) et l'absence de `shell=True`.
