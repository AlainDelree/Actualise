## Issue #64 — Recopie de dist\Actualise vers le partage disparue après résolution manuelle du conflit de fusion (issues #62/#63)

- Vérification approfondie de `build\rebuild_actualise_setup.bat` (étape
  [8/8]) sur `master` (commit `41abad8`, base de ce worktree) : l'étape de
  recopie `robocopy "dist\Actualise" "%ORIGDIR%\dist\Actualise" /MIR ...`
  (issue #62) **est bien présente**, placée avant les étapes issues de
  l'issue #63 (copie vers `%FIXEDSHARE%`) et la copie de
  `dist\ActualiseUI.exe`. Comparaison ligne à ligne (`git diff` entre le
  commit `e36f57b` — état juste après le merge de l'issue #62, avant celui
  de l'issue #63 — et `HEAD`) : le bloc issue #62 (robocopy `dist\Actualise`
  + gestion d'erreur `popd popd exit /b 1`) est identique avant/après le
  merge de l'issue #63, seule une nouvelle étape 8bis (chemin fixe) a été
  insérée entre la copie `dist\Actualise` et la copie
  `dist\ActualiseUI.exe`.
- Le message `[OK]` final reflète bien les trois copies : `echo [OK]
  dist\Actualise\ et dist\ActualiseUI.exe copies vers %ORIGDIR%\dist\`
  suivi de `echo [OK] installeur\output\Actualise-Setup-v9.exe copie vers
  %FIXEDSHARE%\ (chemin fixe)`. Les trois éléments annoncés (dist\Actualise,
  ActualiseUI.exe, setup vers chemin fixe) correspondent bien aux trois
  robocopy exécutées.
- Parenthèses de blocs `if %errorlevel% geq 8 (...)` de l'étape [8/8]
  comptées : 9 ouvrantes / 9 fermantes, aucun bloc orphelin.
- **Aucune modification de code effectuée** : le problème décrit dans
  l'issue (étape manquante suite à la résolution manuelle du conflit) ne
  se retrouve pas dans l'état actuel du fichier sur `master`. Hypothèse la
  plus probable : l'issue a été rédigée sur la base d'une relecture faite
  avant un ajustement ultérieur du merge, ou d'une lecture partielle du
  fichier (la copie `dist\Actualise` est bien présente mais à quelques
  lignes de distance du message `[OK]` qui semblait ne mentionner que deux
  copies au premier coup d'œil, la troisième étant confirmée par la ligne
  `[OK]` suivante).
