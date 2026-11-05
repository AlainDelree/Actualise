# Changelog — issue #87

## Issue #87 — Audit #92 : violations ruff de l'outil d'audit, lot A (formel) puis lot B (examiné une par une)

- **Lot A (formel, sans changement de comportement)** :
  - I001 (imports non triés) : sur les 6 fichiers signalés, seul
    `tests/test_config.py` contenait une véritable inversion
    alphabétique (`chemin_config_portable` avant `charger_config`
    dans l'import groupé depuis `config`) ; corrigée. Les 5 autres
    fichiers (`mise_a_jour.py`, `notifications.py`,
    `tests/test_mise_a_jour.py`, `tests/test_notifications.py`,
    `tests/test_version_check.py`) ont été revérifiés mécaniquement
    (tri Python) contre la convention décrite dans l'issue — sections
    bibliothèque standard / tiers / projet, `import x` avant
    `from x import y`, ordre alphabétique — et sont déjà conformes :
    aucun changement n'y a été apporté.
  - UP012 (`tests/test_notifications.py`) : `"...".encode("utf-8")`
    → `"...".encode()` (UTF-8 étant déjà la valeur par défaut).
  - ISC004 (`tests/test_actualise.py`, deux occurrences identiques,
    commande PowerShell d'un test de verrou de fichier) :
    concaténation implicite volontaire (une seule chaîne coupée sur
    deux lignes) entourée de parenthèses ; valeur de chaîne
    strictement identique.
  - RUF059 (`tests/test_actualise.py`) : variable dépaquetée inutilisée
    `chemin_zip_appele` renommée `_chemin_zip_appele`.
  - SIM117 (`tests/test_actualise.py`, trois occurrences) : blocs
    `with` imbriqués fusionnés en un seul `with` à plusieurs contextes
    (forme parenthésée), même ordre des contextes et mêmes alias.
  - EXE001 (`actualise.py`, `actualise_ui.py`) : aucun changement —
    ce sont des exécutables Windows construits par PyInstaller,
    jamais lancés via leur shebang ; le bit exécutable Linux n'a pas
    de sens ici (détails et options possibles dans le rapport de
    clôture de l'issue).
- **Lot B (examiné un par un, aucun changement de code)** :
  - PLW1510 (`tests/test_actualise.py`, deux occurrences) : les deux
    appels à `subprocess.run` ne capturent pas la valeur de retour
    (`CompletedProcess` non assigné) — le code de retour n'est donc
    jamais lu, et `check=False` n'a pas été ajouté (pas de lecture à
    rendre explicite).
  - SIM115 (`config.py`, `mise_a_jour.py`) : les deux
    `tempfile.NamedTemporaryFile(...)` sont volontairement assignés
    à une variable avant d'être utilisés dans un `with` séparé, pour
    garantir que le fichier est refermé avant un `os.replace`/un
    nettoyage par suppression (contrainte Windows : fichier fermé
    avant remplacement/suppression) ; fusionner en un seul `with`
    aurait changé ce moment de fermeture. Non modifiés.

Non vérifiable dans cet environnement (sans Windows, sans `ruff`) :
le contrôle par `ruff` lui-même, le tri exact des imports selon la
configuration réelle de l'outil d'audit, et tout ce qui touche aux
deux tests Windows de verrou de fichier (`subprocess.run` du bat réel,
fermeture de fichier sous Windows).
