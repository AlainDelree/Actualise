# Changelog — issue #94

## Issue #94 — Ruff : EXE001, SIM115 et UP012 résiduel (retour à 0 erreur)

- EXE001 (`actualise.py`, `actualise_ui.py`) : suppression de la ligne
  shebang `#!/usr/bin/env python3` en tête de fichier. Ces deux fichiers
  sont lancés via PyInstaller ou `python`, jamais directement.
- SIM115 (`config.py`, `mise_a_jour.py`) : code inchangé (`delete=False`
  volontaire pour récupérer le chemin, fichier refermé par le `with`
  juste après) — ajout d'un commentaire expliquant la raison et de la
  directive `# noqa: SIM115` sur la ligne de l'appel
  `tempfile.NamedTemporaryFile(`. Autorisation explicite d'Alain pour ces
  deux `# noqa`. Aucun changement de comportement, notamment dans
  `mise_a_jour.py` (vérification SHA-256 non touchée).
- UP012 : déjà résolue par #93 (le `.encode("utf-8")` de
  `tests/test_notifications.py` ligne 28 avait déjà été remplacé par un
  littéral bytes) — vérifié avant toute modification, ruff ne la
  signalait plus ; aucune action nécessaire sur ce point.
- Vérification : `ruff check --no-cache .` (ruff 0.17.3, outil d'audit)
  passe de 4 erreurs (EXE001 ×2, SIM115 ×2) à 0 erreur, sans RUF100
  nouveau. Suite de tests identique avant/après (88 passed, 10 skipped).
