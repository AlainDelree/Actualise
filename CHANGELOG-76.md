# Changelog — issue #76

## Issue #76 — Audit #92 : épingler la version de requests dans requirements.txt

- `requirements.txt` : `requests` → `requests==2.34.2` (règle EXP-001 de
  l'audit #92 — installation reproductible et contrôle des vulnérabilités
  connues pour l'unique dépendance réseau de l'outil). Version retenue :
  celle installée dans l'environnement Python qui sert à lancer les tests
  de ce worktree (`/home/alain/Bridge_Agent/venv`, premier `python3`/`pytest`
  du `PATH`), relevée via `pip show requests` dans cet environnement —
  c'est aussi la dernière version publiée sur PyPI au moment du constat,
  sans vulnérabilité publique connue identifiée.
- Suite de tests (`pytest tests/`) relancée avec cette version exacte :
  61 passed, 10 skipped — inchangé par rapport à avant épinglage.
- La version embarquée dans l'exécutable Windows actuel n'est plus
  relevable (`build\rebuild_actualise.bat` recrée et supprime son
  environnement de build à chaque exécution). Le prochain build Windows
  installera `requests==2.34.2` : à contrôler une fois par Alain après ce
  build.
