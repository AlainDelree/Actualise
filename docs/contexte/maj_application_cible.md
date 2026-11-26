# Généralisation de la mise à jour à une application cible

**Mise à jour d'une application cible (généralisation).** Le mécanisme
flag + bat décrit dans `docs/contexte/actualiseui_dialogue.md` s'applique
aussi à la mise à jour d'une application cible, pour la même raison
fondamentale que pour Actualise lui-même : son exécutable est, en usage
normal, **toujours en cours d'exécution** au moment où Actualise
voudrait appliquer sa mise à jour (c'est elle qui vient de lancer
Actualise, voir `docs/contexte/vue_ensemble.md`, « Principe de
fonctionnement », et `docs/contexte/bascule_mise_a_jour.md`, « Garde-fou
anti-boucle infinie »). Une extraction directe au démarrage échouerait
donc systématiquement (fichiers verrouillés). Un jeu ne s'auto-met-à-jour
donc jamais par extraction directe : **uniquement** via ce même
mécanisme flag + bat, moyennant les adaptations suivantes :

- **Même fichier flag**, `actualise_update.flag`, même nom, même
  dossier (`repertoire_installation` de l'application cible) : c'est la
  seule chose que le code déjà déployé dans les jeux teste (son nom
  littéral), ils ne savent donc pas distinguer les deux usages — d'où un
  champ facultatif `type` (`"actualise"` ou `"jeu"`) ajouté au JSON du
  flag, purement informationnel (diagnostic humain), que ce code
  existant ignore totalement.
- **Bat écrit sous le dossier d'Actualise, pas dans le dossier du jeu
  (correction issue #84, suite à l'audit #92).** La lecture du code déjà
  déployé côté Scrabble (`chemin_actualise_valide`/
  `traiter_flag_actualise`) a établi que ce code n'accepte une valeur
  `"bat"` lue dans le flag que si elle désigne un fichier `.bat`/`.exe`
  **existant et situé sous `C:\Actualise` (chemin résolu)** — un chemin
  sous le dossier du jeu est donc systématiquement refusé, journalisé
  comme tel au démarrage, et la mise à jour d'un jeu Scrabble ne
  s'applique jamais. Le bat d'un jeu est donc écrit sous
  `config.chemin_config_portable()` (le même dossier où est déjà écrit
  `updater.bat` d'Actualise lui-même), sous le nom
  **`updater_<nom>.bat`** — `<nom>` étant l'identifiant d'application déjà
  utilisé par le code pour `config_<nom>.json` et la zone d'attente — afin
  de ne jamais entrer en collision ni avec `updater.bat` (Actualise
  lui-même) ni avec le bat d'un autre jeu géré par la même installation.
  Le gabarit continue de faire un `cd /d` explicite vers le dossier du
  jeu en tout début de script : toutes les opérations relatives
  (bascule des entrées du zip, journal `updater.log`) restent donc
  appliquées dans le dossier du jeu, inchangé — seul l'emplacement du
  fichier `.bat` lui-même change, tous les chemins qu'il référence
  (zip, flag, config) étant déjà absolus. `<nom>` n'est accepté dans ce
  nom de fichier que s'il est non vide et limité aux lettres
  ASCII/chiffres/`_`/`-` (règle de sécurité : protège contre un nom venu
  de la configuration contenant un séparateur de chemin, `..` ou un
  espace) — un nom invalide est rejeté proprement (log, aucun fichier
  écrit), sans faire planter Actualise. Rummikub, qui ne valide aucun
  dossier pour la clé `"bat"` du flag, n'était pas affecté par ce bug
  mais n'est pas non plus perturbé par ce changement, puisqu'il ne lit
  que le chemin indiqué par le flag, quel qu'il soit. Un ancien
  `updater.bat` laissé dans le dossier du jeu par une version
  antérieure à cette correction est nettoyé au passage suivant (voir
  `_nettoyer_ancien_bat_jeu`), mais seulement s'il porte la marque du
  gabarit jeu d'Actualise et seulement une fois le bat/flag régénérés
  avec succès au nouvel emplacement — un fichier homonyme qui ne porte
  pas cette marque est conservé et signalé dans le journal ; de même, un
  ancien flag de type `"jeu"` dont la clé `"bat"` pointe hors du dossier
  d'Actualise est considéré périmé et régénéré au nouvel emplacement
  (jamais un flag de type `"actualise"`, jamais touché par ce
  nettoyage).
- **Un seul flag à la fois, par dossier.** Le nom de fichier étant
  identique pour les deux usages, un seul type de mise à jour peut être
  en attente de validation/bascule dans le dossier d'une application
  cible donnée à un instant donné. Si le zip d'Actualise **et** celui du
  jeu sont tous deux détectés au même cycle de vérification, Actualise
  occupe le flag en premier (ordre de traitement des cibles) ; la mise à
  jour du jeu est alors reportée à un cycle ultérieur, une fois ce flag
  consommé par le bat d'Actualise.
- **Bat généré dynamiquement selon le contenu du zip**, et non plus
  pour trois noms fixes connus à l'avance (`_internal`/`Actualise.exe`/
  `ActualiseUI.exe`) : Actualise inspecte le zip du jeu au moment de la
  génération (`_lister_entrees_racine_zip`) et génère un bloc de bascule
  renommage+déplacement pour chacune de ses entrées de premier niveau
  (fichiers ou dossiers), avec les mêmes garanties (jamais de
  déplacement direct vers un nom encore existant, restauration complète
  de l'état initial au moindre échec, dans l'ordre inverse des éléments
  déjà basculés). Chaque nom d'entrée est validé avant génération du bat
  (`_entree_racine_jeu_valide`, liste de refus contre l'injection de
  commande dans les blocs batch générés, et depuis l'issue #105 contre
  tout caractère non ASCII — voir `docs/contexte/bascule_mise_a_jour.md`,
  « Noms d'entrées de premier niveau d'un zip de jeu », SEC-024). Un nom
  d'entrée rejeté (zip et empreinte retirés, ni bat ni flag écrits) fait
  aussi sauter la notification ntfy « mise à jour disponible » pour ce
  zip côté `tache_verification_arriere_plan` — elle serait fausse
  (issue #105, point 3) ; le cas « un flag est déjà en attente »
  (mise à jour simplement reportée) continue, lui, d'envoyer cette
  notification. `manifest["supprimer"]` n'est en revanche **pas**
  appliqué par ce bat (contrairement à l'ancienne extraction directe
  qu'il remplace) : limitation connue, le risque d'une implémentation
  batch générique de suppressions ciblées n'étant pas jugé proportionné
  à un besoin non démontré pour un jeu.
- **Attente étendue au jeu lui-même.** Le bat attend la fin non
  seulement de `Actualise.exe`/`ActualiseUI.exe`, mais aussi de
  l'exécutable du jeu (champ `executable` de `config_<nom>.json`), avec
  la même limite de temps et le même abandon sans aucune modification
  si cette limite est atteinte.
- **Pas de relance automatique à la fermeture normale.** Quand le
  gestionnaire de fermeture du jeu (INTEGRATION.md, §6) lance le bat
  directement (sans argument), celui-ci n'essaie jamais de relancer le
  jeu — comportement hérité tel quel du gabarit d'Actualise (`if
  "%~1"=="--relancer" start "" "%~2"`), qui ne s'active que si le bat
  reçoit explicitement `--relancer <exe>`.
- **Cas `--relancer` (fenêtre affichée pendant que le jeu tourne
  encore).** Le seul appelant qui passe `--relancer` est
  `ActualiseUI.exe`, lui-même lancé par le code de **démarrage** du jeu
  (INTEGRATION.md, §6) — jamais par le gestionnaire de fermeture. Cela
  ne peut donc se produire que si le flag a **survécu jusqu'au
  démarrage suivant** du jeu (voir cas limite ci-dessous) : la fenêtre
  de choix s'affiche alors que le jeu est déjà en train de démarrer (et
  continue, sans jamais attendre la fenêtre). Si l'utilisateur clique
  sur « Mettre à jour » à ce moment, le bat est lancé avec `--relancer
  <exe du jeu>` alors que le jeu tourne encore : il attend sa fermeture
  comme n'importe quel autre cas, puis le relance automatiquement une
  fois la bascule terminée — symétrique du comportement déjà existant
  pour Actualise lui-même (relance de l'application cible après la
  bascule d'Actualise).
- **Cas limite : le flag survit jusqu'au démarrage suivant du jeu**
  (ex. extinction du PC avant la fermeture normale du jeu, qui n'a donc
  jamais eu l'occasion de lancer le bat). Le code de démarrage du jeu
  (INTEGRATION.md, §6) relance alors `ActualiseUI.exe` sans savoir que
  le jeu est déjà en cours de démarrage :
  - **« Plus tard »** : ferme simplement la fenêtre, flag conservé —
    aucune perte, le choix sera reproposé au prochain démarrage (ou
    appliqué à la fermeture normale de cette session-ci, comme dans le
    cas courant).
  - **« Mettre à jour »** : le flag est supprimé **avant** le
    lancement du bat (`actualise_ui.py`, fonction `mettre_a_jour`) —
    si le bat n'aboutit pas (le jeu met plus longtemps à se fermer que
    la limite de temps du bat, par défaut 30s, probablement insuffisant
    pour une session de jeu en cours), il abandonne **sans rien
    modifier**, et la mise à jour n'est alors plus associée à aucun
    flag. Elle n'est cependant **pas perdue** : le zip reste en zone
    d'attente, `build_installe` est inchangé, et `_assurer_maj_jeu_en_attente`
    régénère un nouveau bat + flag dès le **prochain lancement** du jeu
    (que ce soit via `tache_verification_arriere_plan`, qui retélécharge
    et retente à chaque cycle tant que la mise à jour n'est pas
    installée, ou via `appliquer_mises_a_jour_en_attente` au lancement
    suivant) — au prix d'un redémarrage supplémentaire avant que la
    mise à jour s'applique réellement, mais sans aucune perte
    définitive. Ce comportement découle directement de la réutilisation
    du mécanisme existant (flag supprimé avant lancement du bat) et
    n'est pas trivial à corriger sans toucher au code déjà déployé dans
    les jeux (hors de ce dépôt).

Ce mécanisme sert donc à la fois à la mise à jour d'Actualise lui-même
et à celle d'une application cible — toujours un seul flag à la fois
par dossier, jamais les deux simultanément.
