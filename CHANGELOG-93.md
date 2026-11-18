# Changelog — issue #93

## Issue #93 — Ruff UP012 : littéral bytes dans tests/test_notifications.py

- Correction (`tests/test_notifications.py`) : remplacement du littéral
  `"un message".encode()` par le littéral bytes équivalent `b"un message"`
  dans `test_envoi_reussi_appelle_post_avec_bonne_url_et_message`, pour
  éliminer la violation Ruff UP012. Aucun changement de comportement.
- Violations EXE001 ×2 et SIM115 ×2 restent en l'état, non traitées dans
  cette issue (décisions d'Alain en attente).
