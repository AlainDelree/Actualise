# Changelog — issue #79

## Issue #79 — Audit #92 : actualise_ui.py, appel sans shell et commentaire du repli TclError

- **SEC-003** : `mettre_a_jour()` (ligne 57 avant modification) lançait
  `updater.bat` via `subprocess.Popen(commande, shell=True)` avec une
  commande assemblée par formatage de chaîne. `updater.bat` n'étant pas
  un exécutable PE, Windows a besoin de `cmd.exe` pour l'interpréter — le
  chemin peut aussi contenir des espaces (d'où les guillemets dans
  l'ancienne chaîne). Remplacé par un appel explicite `cmd /c` avec une
  liste d'arguments (nouvelle fonction `construire_commande_maj`),
  `shell=True` supprimé. Même commande effective, mêmes entrées
  (`--bat`, `--relancer`), comportement inchangé.
- **PRO-012** : commentaire ajouté dans le corps du `except
  tk.TclError: pass` (ligne 46) expliquant que le repli est volontaire
  (`-toolwindow` est un attribut de fenêtre propre à Windows, absent sur
  les autres plateformes). Le commentaire précédent avant le `try` est
  conservé (il explique l'attribut lui-même).
- **Test ajouté** : `tests/test_actualise_ui.py` couvre
  `construire_commande_maj` (sans/avec `--relancer`, forme liste —
  pas de chaîne shell assemblée). Le reste de `actualise_ui.py` dépend
  de Tk/Windows et n'est pas testable sans interface graphique.
- **Non vérifié faute de Windows sur cette machine** : le comportement
  réel de `subprocess.Popen(["cmd", "/c", ...])` au lancement effectif
  d'`updater.bat` (ce dépôt ne dispose que d'un environnement Linux) ;
  vérifié uniquement par lecture de la doc Windows (nécessité de `cmd
  /c` pour les `.bat`) et par test unitaire de la construction de la
  commande.
