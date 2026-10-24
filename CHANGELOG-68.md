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
