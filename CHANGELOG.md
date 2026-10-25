# Changelog — issue #57

# Changelog — issue #73

## Issue #73 — Applique la mise à jour d'un jeu à sa fermeture, avec le mécanisme flag + updater.bat

- **Cause corrigée** (diagnostic issue #72) : l'application cible lance
  `Actualise.exe --config <nom>` par un `Popen` non bloquant à son
  propre démarrage et continue de tourner sans l'attendre — son
  exécutable est donc, en usage normal, **toujours** en cours
  d'exécution au moment où Actualise voulait appliquer sa mise à jour.
  L'extraction directe (`extractall`) échouait alors silencieusement
  (fichiers verrouillés), le zip restant indéfiniment en zone d'attente,
  retéléchargé à chaque lancement sans jamais s'appliquer.
- **Généralisation du mécanisme flag + bat**, jusqu'ici réservé à la
  mise à jour d'Actualise lui-même (issue #36/#68), à la mise à jour
  d'une application cible :
  - `_lister_entrees_racine_zip` inspecte le zip téléchargé et liste ses
    entrées de premier niveau (fichiers/dossiers) ;
  - `_generer_updater_bat_jeu` génère un bat dédié au jeu (dans son
    propre dossier d'installation), avec un bloc de bascule
    renommage+déplacement par entrée (jamais de déplacement direct vers
    un nom encore existant), restauration complète de l'état initial au
    moindre échec, attente réelle de la fin du jeu **et** de
    `Actualise.exe`/`ActualiseUI.exe` (limite de temps, abandon sans
    rien modifier au-delà), journal `updater.log`, et réécriture de
    `build_installe` dans `config_<nom>.json` (sans BOM) seulement après
    bascule confirmée ;
  - `_ecrire_flag_maj` accepte désormais un champ `type_maj`
    (`"actualise"` ou `"jeu"`), ajouté au JSON du flag — facultatif,
    ignoré par le code déjà déployé dans les jeux (seul le nom de
    fichier `actualise_update.flag` compte pour eux) ;
  - `_assurer_maj_jeu_en_attente` orchestre la génération (appelée au
    téléchargement dans `tache_verification_arriere_plan`, et en retry
    au lancement suivant depuis `appliquer_mises_a_jour_en_attente`) ;
    ne fait rien si un flag est déjà présent dans le dossier du jeu — un
    seul type de mise à jour en attente à la fois, celle d'Actualise
    passant toujours en premier (ordre de traitement des cibles).
- **Suppression de l'extraction directe d'un jeu** dans
  `appliquer_mises_a_jour_en_attente` : un zip de jeu ne s'applique plus
  que via ce bat. Si le bat/flag ne peut pas être généré (`OSError`,
  zip invalide), le zip est conservé et l'échec journalisé, sans aucune
  extraction.
- **Non traité par le bat du jeu** : `manifest["supprimer"]` (limitation
  connue et documentée, non demandée par l'issue, risque jugé non
  proportionné pour un gain non démontré) ; application directe sans
  attendre une fermeture du jeu quand Actualise est lancé à la main
  alors que le jeu ne tourne pas (facultatif, non traité — voir rapport
  de clôture de l'issue).
- **Documentation** : CONCEPTION.md corrigé (le raccourci pointe vers le
  jeu, pas vers Actualise ; l'exécutable du jeu tourne bien pendant la
  bascule) et complété (généralisation du mécanisme flag + bat, cas
  limite du flag survivant jusqu'au démarrage suivant du jeu) ;
  INTEGRATION.md complété avec le lancement d'Actualise par le jeu
  (jusqu'ici non documenté) et les deux usages du flag.
- **Tests** : `tests/test_actualise.py` — nouveaux tests de décision
  (flag généré avec le bon contenu pour un jeu, jamais d'extraction
  directe, aucun nouveau flag tant qu'un flag existe, priorité
  d'Actualise sur un jeu au même cycle) et nouvelle classe
  `TestGabaritUpdaterBatJeu` (exécution réelle du bat généré : succès,
  jeu encore ouvert à l'échéance, fichier verrouillé, zip invalide —
  mêmes scénarios que `TestGabaritUpdaterBat`, issue #68, appliqués au
  cas générique d'un jeu).

# Changelog — issue #71

## Issue #71 — build\rebuild_actualise.bat : refuse un numéro de build invalide ou déjà publié

- **Garde-fou étape 1** : `--build N` est désormais refusé, avant toute
  copie/construction/écriture, si `N` n'est pas un entier strictement
  supérieur au build courant de `version.json`, quel que soit le mode
  (avec ou sans `--publier`) — la copie vers le dossier fixe
  `C:\CCW_Share\_derniers_builds\actualise\` a lieu dans les deux cas.
  Message d'erreur indiquant le numéro demandé, le build courant et la
  règle ; code de sortie non nul.
- **`--build` sans valeur** (ou suivi d'un autre argument reconnaissable
  comme non numérique) est refusé avec un message explicite, au lieu
  d'être ignoré silencieusement (le script ne retombe plus sur le numéro
  automatique sans le dire).
- **Argument inconnu** refusé avec la liste des arguments acceptés
  (`--publier`, `--build N`), au lieu d'un simple avertissement suivi
  d'une construction sans publication.
- **Commentaire d'en-tête** décrivant `--build` mis à jour pour indiquer
  la règle de numéro strictement croissant et le refus des arguments
  invalides.
- **Essais réalisés** (PowerShell, depuis la racine du worktree) :
  refus rapides et sans écriture pour `--build 11` (égal au build
  publié), `--build 10` (inférieur), `--build abc` (non numérique),
  `--build` seul (sans valeur), `--publier --build 11` (déjà publié,
  avec publication), et un argument inconnu (`--publierX`) — les six cas
  sortent avec un code 1 avant toute construction, `version.json`
  inchangé (`git diff` vide) et rien de nouveau dans
  `installeur\output`. Essai accepté sans `--publier` avec `--build 99`
  (numéro fictif, jamais utilisé en publication) : installeur et archive
  construits avec succès, copiés dans `installeur\output\` du worktree
  et dans le dossier fixe du partage — fichiers à supprimer à la main
  par Alain. `version.json` reste inchangé dans toute cette issue
  (aucun `--publier` utilisé pendant les essais).

# Changelog — issue #70

## Issue #70 — Renomme le script de build unifié en rebuild_actualise.bat et retire les anciens scripts

- **Renommage** : `build\rebuild_actualise_unifie.bat` (issue #67) devient
  `build\rebuild_actualise.bat`. L'ancien `rebuild_actualise.bat` (build
  d'`Actualise.exe` seul, sans installeur ni archive) est supprimé
  d'abord. En-tête et messages d'aide réécrits pour décrire le script tel
  qu'il est, sans « provisoire » ni mention des anciens scripts.
- **Suppression** de `build\rebuild_actualise_setup.bat` et de
  `build\publier_actualise.bat` (leurs fonctions sont couvertes par le
  script unique depuis l'issue #67).
- **Références nettoyées** : `.gitignore` (note sur `git add -f`,
  réduite à l'unique script restant), `installeur\actualise.iss`
  (commentaire de compilation, mention VM/VirtualBox/VBOXSVR remplacée
  par une description du staging local). `actualise.spec` citait déjà le
  nom définitif, aucun changement nécessaire.
- **Essai réalisé** sans `--publier`, avec `--build 99` (numéro fictif,
  jamais utilisé en publication) : installeur et archive construits avec
  succès, copiés dans `installeur\output\` du worktree et dans
  `C:\CCW_Share\_derniers_builds\actualise\` ; structure de l'archive
  identique à la Release v11 (31 entrées, 4 éléments à la racine) ;
  `version.json` inchangé (vérifié par `git diff` vide).
- **Fonctions des anciens scripts non reprises dans le script unique**
  (signalées, non corrigées dans cette issue) : construction d'
  `Actualise.exe` seul avec recopie de `dist\` (ancien
  `rebuild_actualise.bat`), recopie de `dist\Actualise` et
  `dist\ActualiseUI.exe` vers le worktree (ancien
  `rebuild_actualise_setup.bat`), et refus d'un numéro de build
  inférieur ou égal à celui de `version.json` lors de la publication
  (ancien `publier_actualise.bat`).

Fichiers de test (build 99) laissés dans
`C:\CCW_Share\_derniers_builds\actualise\` : à supprimer à la main par
Alain, hors du périmètre de l'agent.

# Changelog — issue #68

## Issue #68 — updater.bat fiabilisé : attente réelle, contrôle de chaque étape, journal, ActualiseUI.exe basculé

Contexte : aucun incident constaté (observation réelle v10→v11 confirmant
que le bat avait fonctionné correctement) — issue préventive, basée sur la
lecture du gabarit `_GABARIT_UPDATER_BAT` (`actualise.py`), inchangé depuis
la v10.

- **Attente réelle des processus** : le bat scrute désormais `tasklist`
  pour `Actualise.exe` et `ActualiseUI.exe` (toutes les secondes, limite
  30 s par défaut, surchargeable par la variable d'environnement
  `ACTUALISE_UPDATER_MAX_ATTENTE` — utilisé par les tests pour rester
  rapides) au lieu d'un délai fixe de 5 s. Si l'un des deux tourne encore
  à l'échéance, le bat abandonne **sans rien modifier**.
- **Chaque étape contrôlée** (extraction, renommage, déplacement) pour les
  trois éléments `_internal`, `Actualise.exe` et `ActualiseUI.exe` (ce
  dernier n'était jamais remplacé par l'ancien gabarit — constaté sur le
  PC utilisateur : `ActualiseUI.exe` gardait la date du build 10 après une
  mise à jour vers la v11). Tout échec restaure l'installation dans son
  état initial (annulation dans l'ordre inverse des étapes déjà
  effectuées), conserve le zip et ne touche jamais `build_installe`.
- **Déplacement toujours vers un nom libéré** : chaque élément est
  renommé en `.old` avant que le nouveau ne soit déplacé à sa place —
  jamais un déplacement direct vers un nom de dossier encore existant.
  Hypothèse de l'issue **confirmée** par un test manuel direct sur ce
  PC : `move` d'un dossier vers un dossier de même nom déjà présent place
  le premier **à l'intérieur** du second au lieu de le remplacer. Avec le
  renommage préalable, ce cas ne peut plus se produire.
- **`build_installe` réécrit, puis zip et flag supprimés, seulement après
  bascule confirmée** des trois éléments — jamais avant, jamais en cas
  d'échec (déjà vrai pour `build_installe` depuis l'issue #66, mais pas
  pour l'ordre entre bascule et suppression du zip/flag en cas d'échec
  partiel après extraction).
- **Journal `updater.log`**, dans le dossier d'Actualise, une ligne
  horodatée par étape/échec/abandon ; tronqué aux 200 dernières lignes
  dès qu'il dépasse 100 Ko pour rester borné d'une exécution à l'autre.
- **Chemin de bascule par renommage silencieuse (`_basculer_par_renommage`,
  garde-fou anti-boucle infinie) vérifié** : il ne présente **pas** le même
  défaut. `ActualiseUI.exe` y est déjà basculé correctement (boucle
  générique sur tous les fichiers extraits, `Actualise.exe` étant le seul
  cas particulier nécessitant le renommage en deux temps) ; tout `OSError`
  (fichier verrouillé) y est déjà intercepté sans toucher
  `build_installe` ni supprimer le zip. Rien à corriger sur ce chemin.
- **Rôle ni déclenchement du bat inchangés** : toujours généré par
  `tache_verification_arriere_plan`, toujours lancé par
  `ActualiseUI.exe`/l'application cible via le flag, toujours relancé via
  `--relancer` en cas de succès.

### Tests ajoutés (`tests/test_actualise.py`, classe `TestGabaritUpdaterBat`)

Exécution réelle du `updater.bat` généré (pas de mock) dans un dossier
temporaire, sur Windows (`os.name == "nt"`) :
- succès : les trois éléments sont remplacés, `build_installe` passe à
  11, zip et flag supprimés, journal contient les lignes de succès ;
- zip invalide : rien n'est modifié (comparé à l'état initial), zip et
  flag conservés, journal contient l'échec d'extraction ;
- fichier verrouillé (`Actualise.exe` ouvert en exclusif par un
  processus séparé pendant l'exécution du bat) : `_internal` déjà
  basculé à ce stade est restauré, l'installation entière revient à son
  état initial, journal contient le verrouillage et la restauration ;
- processus `Actualise.exe`/`ActualiseUI.exe` encore en cours (simulé par
  une copie renommée de `ping.exe`, détectée par `tasklist` comme tout
  autre processus de ce nom) : abandon sans modification si le délai
  maximal est dépassé, et bascule réussie si le processus se termine
  avant l'échéance.

### Limite rencontrée

Le module `requests` (dépendance du projet, `requirements.txt`) n'est pas
installé dans cet environnement d'exécution et aucun accès réseau n'est
autorisé pour cette issue (`RESEAU: non`) : je n'ai pas pu l'installer.
J'ai donc utilisé un stub local minimal de `requests` (placé hors du
dépôt, uniquement dans `PYTHONPATH` pour la durée des tests, jamais
committé) afin de pouvoir exécuter réellement la suite `pytest`
existante et les nouveaux tests. Résultat : 25 tests passent, 2 échecs
déjà présents avant mes modifications (confirmé par comparaison avec le
code d'origine remis en place temporairement via `git stash` — fuite de
handle de fichier de `logging` entre tests Windows, sans rapport avec
cette issue, hors périmètre).

## Issue #69 — Mise à jour ETAT.md et TACHES.md après la publication d'Actualise v11

- ETAT.md : « Versions publiées » passe de v10 à v11, précise que la
  Release v11 contient DEUX assets (installeur + archive), retire la
  phrase sur le non-republiement de l'installeur et la mention
  d'Actualise-Setup-v9.exe.
- ETAT.md : procédure de déploiement mise à jour pour utiliser
  Actualise-Setup-v11.exe (Release v11).
- ETAT.md : nouvelle section « Processus de build et de publication »
  (build\rebuild_actualise_unifie.bat --publier, ordre de publication
  manuel recommandé).
- ETAT.md : « Points en suspens » complété (renommage du script de
  build, fiabilisation de updater.bat dont ActualiseUI.exe, intégration
  de CHANGELOG-67.md, test réel de mise à jour d'un jeu à venir) ; le
  point sur la cause de l'échec d'extraction est conservé tel quel.
- TACHES.md : l'entrée sur les noms d'assets versionnés (réalisée) est
  retirée et remplacée par les quatre tâches restantes listées ci-dessus.

Aucun code ni test touché — documentation uniquement.

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

# Changelog — issue #66

## Issue #66 — build_installe périmé après mise à jour par fenêtre, échec d'extraction fatal, ETAT.md obsolète

- **build_installe (point 1).** Le worktree reprenait un travail déjà
  entamé par une tentative précédente de cette même issue :
  `_generer_updater_bat` prenait déjà un paramètre `build` et le bat
  généré réécrivait déjà `build_installe` dans `config_actualise.json`
  via PowerShell, *après* la bascule effective de `Actualise.exe`/
  `_internal` et *avant* la suppression du zip source (évite le piège
  signalé dans l'issue : écrire le nouveau numéro trop tôt aurait fait
  voir le zip encore en attente comme un résidu obsolète et le
  supprimer). Écriture sans BOM (`UTF8Encoding($false)`), cohérente avec
  `config._ecrire_json_atomique`. **Mais le site d'appel dans
  `tache_verification_arriere_plan` n'avait pas été mis à jour** :
  `_generer_updater_bat` y était toujours appelé avec 3 arguments au
  lieu de 4, ce qui levait un `TypeError` à chaque mise à jour
  d'Actualise détectée — silencieusement avalé par le `except Exception`
  englobant de la tâche de fond, donc invisible dans les tests existants
  (le zip était déjà renommé en zone d'attente avant l'appel fautif, les
  assertions sur ce renommage passaient malgré tout). Corrigé en passant
  `build_distant` en 4ᵉ argument (`actualise.py`, dans
  `tache_verification_arriere_plan`). Solution restée localisée (un seul
  fichier, pas de nouveau processus ni de refonte du flux de bascule),
  conformément à la contrainte de l'issue.
- **Échec d'extraction non fatal pour l'application cible (point 2).**
  `mise_a_jour.extraire_zip`/`appliquer_manifeste` pour l'application
  cible n'étaient protégés contre aucune `OSError` dans
  `appliquer_mises_a_jour_en_attente` : une `PermissionError` (droits
  insuffisants en Program Files, ou fichier verrouillé parce que
  l'application — qui lance Actualise à son démarrage — tourne encore)
  remontait telle quelle et faisait planter Actualise (fenêtre Windows
  « Unhandled exception »). Entouré d'un `try/except OSError` : log
  `ERROR` explicite (cause probable, chemin concerné), zip conservé pour
  nouvelle tentative, `build_installe` non modifié, `continue` vers la
  cible suivante sans exception — même pattern déjà en place pour
  l'échec de renommage côté Actualise lui-même
  (`_basculer_par_renommage`).
  Vérification préalable (dossier inscriptible / exécutable principal
  non verrouillé) **évaluée mais non implémentée** : le cas réellement
  observé en octobre 2026 concernait un fichier verrouillé *dans une
  sous-arborescence* (`clr_loader\ffi\dlls\amd64\ClrLoader.dll`), pas
  l'exécutable principal — une vérification limitée au dossier racine
  ou à l'exécutable principal ne l'aurait pas détecté, et vérifier
  chaque fichier de l'archive avant extraction serait à la fois plus
  complexe et sujet à une course (TOCTOU) entre la vérification et
  l'extraction réelle. Le `try/except` protège déjà contre ce cas et
  tout autre, sans ce risque ni cette complexité.
- **Tests de non-régression.** Deux tests ajoutés dans
  `tests/test_actualise.py` :
  - `test_echec_extraction_application_cible_zip_conserve_aucune_exception`
    (classe `TestAppliquerMisesAJourEnAttente`) : simule une `PermissionError`
    lors de l'extraction, vérifie qu'aucune exception ne remonte, que le
    zip est conservé, que `build_installe` reste inchangé et qu'un log
    `ERROR` mentionnant l'extraction est émis.
  - `test_bat_updater_genere_avec_le_build_reellement_telecharge`
    (classe `TestTacheVerificationArrierePlan`) : vérifie que
    `_generer_updater_bat` est appelé avec le build réellement
    téléchargé comme dernier argument. Confirmé que ce test échoue sans
    le correctif du site d'appel (vérifié manuellement en reproduisant
    temporairement l'appel à 3 arguments).
  - Suite complète : 58 tests passent (`python3 -m pytest tests/`).
- **ETAT.md** mis à jour : Actualise v10 publié (Release contenant
  uniquement `actualise-v10.zip`, pas l'installeur), Scrabble v13 et
  Rummikub v13 publiés, rappel que les anciennes versions de Rummikub
  (v7 et antérieures, raccourci vers `Actualise.exe`) ne peuvent pas se
  mettre à jour seules vers la nouvelle architecture et exigent une
  installation manuelle du setup courant, rappel renforcé de la nécessité
  de supprimer `C:\Actualise\` avant réinstallation sur un ancien PC
  (`Actualise-Setup.exe` ne réécrit pas un `config_actualise.json`
  existant), et ajout du point ouvert sur la cause exacte (droits ou
  verrouillage) de l'échec d'extraction en Program Files, à trancher par
  un test en conditions réelles.

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

## Issue #63 — Toujours recopier les artefacts de build vers un chemin fixe sur le partage

- `build\rebuild_actualise_setup.bat` (étape [8/8]) : en plus de la copie
  existante vers `%ORIGDIR%\installeur\output\` (dépendante du worktree
  d'où le script est lancé), ajoute une seconde copie systématique de
  `Actualise-Setup-v<N>.exe` vers un chemin fixe et prévisible sur le
  partage : `C:\CCW_Share\_derniers_builds\actualise\`. Ce chemin est
  identique quel que soit le worktree d'origine — plus besoin de
  chercher sur le partage où l'installeur a atterri. Écrase sans
  confirmation le fichier déjà présent (comportement voulu : toujours le
  dernier artefact produit). Le comportement existant (copie vers
  `ORIGDIR`) est conservé tel quel. Documenté en tête de fichier
  (commentaire de l'étape 1).
- Testé avec un build factice, entièrement en bac à sable à l'intérieur
  du worktree (dossiers `origdir`/`fixedshare` simulant `ORIGDIR` et le
  chemin fixe) : les deux copies aboutissent, le chemin fixe est créé
  automatiquement par `robocopy` s'il n'existe pas encore, et une
  seconde exécution avec un contenu différent écrase silencieusement le
  fichier précédent au chemin fixe — confirmant qu'il contient toujours
  le dernier artefact produit.
- `build\publier_actualise.bat` (demandé par l'issue #62) **non
  modifié** : ce fichier n'existe pas encore sur la branche
  `worktree-issue-63` (issue #62 n'est pas encore mergée dans `master`,
  il vit uniquement sur `worktree-issue-62`). Fusionner du contenu
  d'une autre branche non mergée dans ce worktree sortait du périmètre
  de cette tâche. À traiter séparément, soit en appliquant le même
  correctif sur `worktree-issue-62` avant sa fusion, soit via une
  nouvelle issue une fois `publier_actualise.bat` présent sur `master`.

## Issue #62 — Implémenter build\publier_actualise.bat selon le plan diagnostiqué

- `build\rebuild_actualise_setup.bat` (étape [8/8]) : recopie désormais
  aussi `dist\Actualise\` (`/MIR`) et `dist\ActualiseUI.exe` vers le
  partage, en plus du setup compilé — `dist\` reste disponible après le
  build pour `publier_actualise.bat`, sans jamais réinstaller le setup.
- `build\publier_actualise.bat` (nouveau) : construit
  `installeur\output\actualise-v<N>.zip` et son `manifest.json` à partir
  de `dist\` (staging jetable `build\_staging_publication\`), affiche le
  SHA-256 en minuscules prêt à copier dans `version.json`, et rappelle
  explicitement les 2 étapes qui restent manuelles (`version.json` +
  `git push`, `gh release create`). Vérifications préalables : paramètre
  `%1` numérique obligatoire, `%1` strictement supérieur au build déjà
  publié, présence des 3 artefacts `dist\` attendus.
- Testé de bout en bout avec un `dist\` factice (build 11) : zip
  contenant exactement les 3 éléments + `manifest.json` (pas de dossier
  imbriqué), SHA-256 affiché vérifié indépendamment via `Get-FileHash`,
  et les 4 cas d'échec (paramètre absent, non numérique, build ≤
  publié, `dist\` absent) échouent proprement sans zip partiel.

# Changelog — issue #61

- Documentation (`CONCEPTION.md`, sections « Distribution des binaires —
  GitHub Releases » et « Décisions actées ») : correction du nommage
  d'asset documenté, qui décrivait un nom fixe sans numéro de version
  (`<préfixe>.zip`, réécrasé à chaque Release) alors que le code
  (`actualise.py::_url_asset_release`) construit et a toujours construit
  un nom versionné `<préfixe>-v<build>.zip` (ex. `actualise-v48.zip`,
  cohérent avec `_GABARIT_URL_RELEASE`). La documentation reflète
  désormais le comportement réel du code, avec l'explication du choix :
  cohérence avec le nommage déjà utilisé pour les applications cibles
  (ex. `Scrabble-Setup-v10.exe`), pas de dépendance à une URL « latest »
  puisque la publication reste pilotée manuellement par Alain. Aucun
  changement de code.

- Correction (`actualise.py`, `appliquer_mises_a_jour_en_attente`) : lecture
  de `manifest.json` extrait du zip en zone d'attente désormais décodée en
  `utf-8-sig` au lieu de `utf-8` strict, pour tolérer un BOM UTF-8 (InnoSetup
  peut écrire du JSON avec BOM, cf. issue #46 pour `config.py`). Corrige un
  crash au démarrage (`JSONDecodeError: Unexpected UTF-8 BOM`) confirmé en
  conditions réelles.
- Ajout d'un test de non-régression dans `tests/test_actualise.py`
  (`test_manifest_avec_bom_utf8_est_lu_correctement`), sur le modèle du test
  équivalent de `tests/test_config.py` pour l'issue #46.

