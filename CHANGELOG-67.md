# Changelog — issue #67

## Issue #67 — Script de build unique d'Actualise avec --publier, sur le modèle de Rummikub

- **Nouveau script `build\rebuild_actualise_unifie.bat`** (nom provisoire :
  `rebuild_actualise.bat` est déjà pris par le script à conserver ; le
  renommage sera une issue ultérieure), ajouté avec `git add -f` comme les
  trois scripts existants. Construit en une seule exécution
  `Actualise.exe`, `ActualiseUI.exe`, l'installeur `Actualise-Setup-v<N>.exe`
  et l'archive `actualise-v<N>.zip` ; avec `--publier`, écrit en plus
  `version.json` (build + SHA-256 de l'archive finale) et fait un commit
  local (jamais de push, jamais de Release). Numéro de build par défaut =
  celui de `version.json` + 1, ou imposé par `--build N`.
- **Modèle repris de `build\rebuild_rummikub.bat`** (dépôt AlainDelree/Rummikub,
  branche master) et du guide `BUILD_WINDOWS_CCW.md` (dépôt Bridge_Agent),
  tous deux lus par téléchargement HTTP direct. La partie "clone partagé /
  reset git" de la fin du script Rummikub (étape 8, spécifique à un dépôt
  partagé entre workflows, pas à un worktree) n'a pas été reprise : le
  worktree de build local (`C:\Temp\ActualiseBuild`) est simplement nettoyé
  par `rmdir /s /q`.
- **Écarts volontaires par rapport aux trois scripts existants** (décisions
  de l'issue, confirmées par Alain) :
  - Recherche d'Inno Setup dans l'ordre `C:\CCW\tools\InnoSetup6\ISCC.exe`,
    puis les emplacements déjà utilisés par `rebuild_actualise_setup.bat`
    (PATH, Program Files (x86)/Program Files, `C:\.tools\InnoSetup6`), puis
    `.tools\InnoSetup6` du dépôt — message d'erreur listant les six
    emplacements essayés.
  - Aucun `taskkill` : si `Actualise.exe`/`ActualiseUI.exe` tourne, le
    script le signale mais ne l'arrête jamais (il ne l'a pas lancé).
  - Copie finale vers `C:\CCW_Share\_derniers_builds\actualise\` avec le
    **numéro de build réel** dans les deux noms de fichiers
    (`Actualise-Setup-v<N>.exe` et `actualise-v<N>.zip`) : plus aucun nom ni
    numéro codé en dur (`9` dans l'ancien `.iss`/`rebuild_actualise_setup.bat`).
  - Aucune mention de VM ni de partage VirtualBox dans les commentaires.
  - Le script affiche lui-même, en fin d'exécution, les informations situées
    hors du worktree (emplacement d'Inno Setup utilisé, tailles non
    compressées de `dist\Actualise` et `ActualiseUI.exe`, noms et tailles
    des deux fichiers copiés vers le dossier fixe) : l'agent ne liste ni ne
    lit ces dossiers lui-même.
- **Correction apportée pendant l'essai** : la recherche d'ISCC.exe, écrite
  d'abord avec des blocs `if/else (...)` imbriqués, échouait
  systématiquement (`\Inno was unexpected at this time`) parce que la
  *valeur* de `%ProgramFiles(x86)%` contient elle-même des parenthèses, ce
  qui casse le comptage de parenthèses que `cmd.exe` fait sur tout le bloc
  avant de l'exécuter — y compris quand la variable concernée est recopiée
  au préalable dans une variable au nom "propre". Corrigé en réécrivant
  cette étape sous forme plate (`if ... goto`, sans aucun bloc parenthésé).
- **Essai de build réalisé et réussi** : build 11, les 4 artefacts produits,
  structure de l'archive comparée à la Release v10 (31 entrées au total,
  4 éléments à la racine, 25 fichiers + 3 dossiers vides sous `_internal`,
  `manifest.json` sans BOM UTF-8). `version.json` écrit par l'essai
  (`{"build": 11, "sha256": "742...c899"}`) puis son commit annulé par
  `git revert` (jamais de `git reset`) : le dernier état de `version.json`
  sur la branche est de nouveau identique à celui de master avant l'issue
  (`{"build": 10, "sha256": "699...97c7"}`).
- **Scripts existants** (`rebuild_actualise.bat`, `rebuild_actualise_setup.bat`,
  `publier_actualise.bat`) et `installeur\actualise.iss` : non modifiés,
  conservés tels quels.
