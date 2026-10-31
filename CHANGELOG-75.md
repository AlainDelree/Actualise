# Changelog — issue #75

## Issue #75 — rebuild_actualise.bat : refuse un numero a zero initial et corrige l'ordre du rappel de fin

- **Controle de `--build N`** (ligne 52) : la forme `^[0-9][0-9]*$`
  acceptait un numero a zero initial (ex. `014`), qui aurait ete ecrit
  tel quel dans `version.json` avec `--publier` (`"build": 014`, JSON
  invalide). Remplacee par `^[1-9][0-9]*$`, comme Scrabble. Message
  d'erreur et code de sortie `1` inchanges.
- **Rappel de fin affiche avec `--publier`** : l'ordre annonce (1. git
  push, 2. creer la Release) laissait entendre qu'on pouvait annoncer un
  build aux clients via `git push` avant que la Release existe. Remplace
  par l'ordre du guide `BUILD_WINDOWS_CCW.md` : 1. fusionner la branche du
  worktree dans `master` sans pousser, 2. creer la Release `vN` avec
  l'installeur et l'archive, 3. pousser `master`. La phrase rappelant que
  le script ne fait jamais `git push` ni `gh release create` est
  conservee.
- Rien d'autre modifie dans `build\rebuild_actualise.bat` (ASCII, CRLF,
  inchanges).
