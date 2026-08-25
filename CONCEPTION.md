# Conception — Programme Actualise

## Contexte et objectif

Système de mise à jour automatique générique, pensé initialement pour
Scrabble mais conçu pour être réutilisable sur d'autres projets. Permet à
un utilisateur final (ex. la maman d'Alain) de toujours disposer de la
dernière version stable d'une application Windows packagée en .exe
(PyInstaller ou autre), sans réinstallation manuelle à chaque mise à jour.

## Principe de fonctionnement

Un exécutable séparé de l'application cible (contournement du problème
classique : un .exe ne peut pas se remplacer lui-même pendant qu'il
s'exécute). Le raccourci Bureau/menu Démarrer de l'utilisateur final
pointe vers Actualise, jamais directement vers l'application cible —
sinon la mise à jour ne se déclenche jamais.

## Format de version — `version.json`

La comparaison de version se fait via un **entier incrémental**
(compteur de build), pas une chaîne semver ni une comparaison de
chaînes brute :

```json
{"build": 47, "sha256": "<hash hexadécimal du zip publié pour ce build>"}
```

Comparaison : `distant.build > local.build`.

Le champ `sha256` porte sur le **zip complet** (l'asset de Release tel
que publié), pas sur son contenu individuel une fois extrait — c'est un
hash de vérification de l'intégrité du téléchargement, pas du contenu
applicatif (voir « Séquence de démarrage » pour son usage).

**Piège explicite à éviter** : comparer `version.json` comme des
chaînes de caractères donne un résultat lexicographiquement incorrect
(ex. la chaîne `"9"` est jugée supérieure à `"10"`). L'entier
incrémental élimine ce piège par construction et reste trivial à
générer à chaque publication (incrémentation simple).

### Deux fichiers `version.json` distincts

- Un `version.json` dans le **dépôt Actualise** — version d'Actualise
  lui-même.
- Un `version.json` dans le **dépôt de chaque application cible** (ex.
  Scrabble) — l'URL de ce fichier est construite à partir des
  informations du fichier `config_<nom_app>.json` local (dépôt GitHub
  cible).

Les deux logiques de mise à jour (Actualise vs application cible) sont
**indépendantes** : chacune a son propre `build` courant, sa propre
vérification réseau, son propre téléchargement.

## Distribution des binaires — GitHub Releases

Les binaires (Actualise et applications cibles) sont distribués comme
**assets de GitHub Releases**, pas commités dans l'historique git.
Téléchargement via l'URL stable :

```
github.com/<owner>/<repo>/releases/download/<tag>/<fichier>
```

L'asset de Release n'est **pas un exécutable nu** : une mise à jour peut
comporter plus que le seul exécutable (données, dictionnaires, DLL
éventuelles). L'asset est donc une **archive zip** regroupant l'ensemble
des fichiers nécessaires à cette version, ainsi que le manifeste de mise
à jour (voir « Manifeste de mise à jour » ci-dessous) — **un seul asset
par tag de version**, quel que soit le nombre de fichiers concernés.

**Nom de fichier de l'asset : fixe, sans numéro de version.** L'asset
publié pour chaque Release porte toujours le même nom :
**`<préfixe>.zip`** (ex. `actualise.zip`, `scrabble.zip`) — jamais de
numéro de build dans le nom du fichier lui-même. Le numéro de version
vit uniquement dans le **tag** de la Release, au format **`v<build>`**
(ex. `v48`), directement dérivé de l'entier incrémental déjà acté (voir
« Format de version »). Conséquence pratique : chaque nouvelle Release
doit re-uploader un asset portant exactement ce nom fixe pour être
trouvé par Actualise — c'est le tag qui change d'une Release à l'autre,
jamais le nom de fichier de l'asset.

Un diff binaire a été **écarté** : gain marginal face à la complexité
ajoutée, les binaires PyInstaller étant recompilés en quasi-totalité à
chaque changement de code (peu de contenu partagé d'une version à
l'autre pour qu'un diff soit rentable).

`version.json`, à l'inverse, reste un **petit fichier commité
normalement** dans le dépôt (pas un asset de Release) — il doit rester
trivialement accessible via `raw.githubusercontent.com` sans passer par
l'API Releases.

## Manifeste de mise à jour

Chaque archive zip de Release inclut, à sa racine, un fichier
`manifest.json` déclarant le build et les fichiers obsolètes à nettoyer
après extraction :

```json
{"build": 47, "supprimer": ["ancien_dictionnaire.txt", "config_v1.ini"]}
```

- `build` : entier incrémental, cohérent avec le `version.json` déjà
  acté (voir « Format de version »).
- `supprimer` : liste **optionnelle** de chemins relatifs (au dossier
  d'installation) à supprimer après extraction du zip. C'est une **liste
  noire explicite** : seuls les chemins listés sont supprimés, rien
  d'autre n'est touché — **fail-safe** par construction, puisqu'un oubli
  dans cette liste laisse au pire un fichier obsolète inoffensif sur le
  disque, jamais une perte de données par suppression involontaire
  (contrairement à une logique de liste blanche, où un oubli pourrait
  effacer un fichier qui aurait dû être conservé).

**Choix écarté : script exécutable (`.bat` / `.sh`) en post-traitement.**
Un manifeste JSON déclaratif a été préféré à un script pour deux
raisons :

- **Portabilité Linux/Windows** : un `.bat` n'a pas d'équivalent direct
  côté Linux, ce qui imposerait une double maintenance (`.bat` et `.sh`)
  incompatible avec la réutilisabilité Linux visée par le projet.
- **Sécurité** : exécuter un script téléchargé sans supervision de
  l'utilisateur ouvre une surface de risque bien plus large qu'une
  simple opération de suppression bornée à une liste de chemins
  explicites — le manifeste JSON ne permet structurellement rien d'autre
  que cette suppression bornée.

**Cas limite : `manifest.json` absent de l'archive.** Traité comme
**bloquant** : la bascule de cette mise à jour échoue et n'est pas
appliquée (ni extraction, ni suppression, ni lancement de la version
mise à jour). Le zip **n'est pas supprimé** de `zone_attente` — une
nouvelle tentative pourra avoir lieu à un lancement ultérieur si le zip
est re-téléchargé (comportement précis de récupération, ex. nouvelle
tentative immédiate ou attente du prochain cycle de fond, à préciser
côté implémentation). Raison de ce choix : un zip sans manifeste est
considéré **malformé** plutôt que de supposer silencieusement « rien à
supprimer » — un manifeste manquant est plus probablement le signe d'un
problème de publication (asset incomplet, erreur de packaging) qu'une
intention volontaire de l'auteur de la Release.

## Contenu des fichiers de configuration — `config_actualise.json` / `config_<nom_app>.json`

**Historique** : la conception initiale (issues #3/#4/#7) prévoyait un
`config.json` unique regroupant les deux blocs `actualise` et
`application_cible`. Ce format à fichier unique a été **abandonné**
(issue #35) au profit de **deux fichiers séparés**, dans le cadre du
passage au modèle « instance unique partagée » décrit en
« Configuration portable » ci-dessous — voir aussi « Points de
vigilance connus » pour l'historique complet de ce changement. Le
format ci-dessous est celui **actuellement chargé** par
`config.charger_config(nom_app)`.

**`config_actualise.json`** — un seul exemplaire, **partagé** par
toutes les applications cibles gérées par cette installation
d'Actualise :

```json
{
  "build_installe": 12,
  "depot_github": "AlainDelree/Actualise",
  "zone_attente": "C:\\Actualise\\attente\\"
}
```

**`config_<nom_app>.json`** — un exemplaire **par application cible**
(ex. `config_scrabble.json`, `config_rummikub.json`), `nom_app`
correspondant à l'argument `--config <nom>` passé à Actualise (voir
« Configuration portable ») :

```json
{
  "nom": "Scrabble",
  "depot_github": "AlainDelree/Scrabble",
  "build_installe": 47,
  "repertoire_installation": "C:\\Scrabble\\",
  "executable": "Scrabble.exe",
  "icone": "C:\\Scrabble\\Scrabble.ico",
  "topic_ntfy": "actualise-scrabble"
}
```

`config.charger_config(nom_app)` lit les deux fichiers et les fusionne
en un seul dict `{"actualise": ..., "application_cible": ...,
"zone_attente": ..., "topic_ntfy": ...}`, compatible avec la structure
déjà utilisée par le reste d'Actualise (`zone_attente` extrait de
`config_actualise.json`, `topic_ntfy` copié depuis
`application_cible` par commodité pour l'appelant). L'absence de l'un
ou l'autre fichier, ou un JSON malformé, reste **bloquant** :
`FileNotFoundError`/`json.JSONDecodeError` remontent telles quelles,
sans repli silencieux (cohérent avec le choix déjà acté pour l'ancien
`config.json` unique).

Détail des champs :

- `build_installe` (dans `config_actualise.json` **et** dans
  `config_<nom_app>.json`, séparément) : le numéro de build
  actuellement installé pour ce programme, directement comparable au
  champ `build` du `version.json` correspondant (voir « Format de
  version »).
- `depot_github` (dans `config_actualise.json` **et** dans
  `config_<nom_app>.json`) : sert à construire l'URL du `version.json`
  correspondant (voir « Deux fichiers `version.json` distincts »).
- `executable` (dans `config_<nom_app>.json`) : nom/chemin du fichier
  exécutable de l'application cible, une fois la bascule éventuelle
  effectuée (étape 3 de la « Séquence de démarrage »).
- `repertoire_installation` (dans `config_<nom_app>.json`) : dossier
  cible pour l'extraction du zip de mise à jour de l'application
  cible ; c'est aussi dans ce dossier — celui de l'application cible,
  pas celui d'Actualise — qu'est écrit `actualise_update.flag` (voir
  section dédiée à `ActualiseUI.exe` ci-dessous).
- `icone` (dans `config_<nom_app>.json`, **optionnel**) : chemin vers
  le fichier `.ico` de l'application cible, déployé par le setup de
  cette application à un emplacement connu (ex. à côté de son
  exécutable). Ce champ est **informationnel/documenté pour Actualise**
  — Actualise n'a pas d'interface graphique et ne le lit **pas** au
  runtime — mais sert de **convention** pour le setup de l'application
  cible : le même chemin `.ico` doit être utilisé à la fois pour ce
  champ et pour le champ `IconFilename` du raccourci créé par ce setup
  (voir « Intégration avec le setup.exe d'une application cible »),
  afin que la documentation de `config_<nom_app>.json` reste cohérente
  avec l'icône réellement affichée par le raccourci.
- `zone_attente` (dans `config_actualise.json` uniquement) : chemin du
  dossier où sont stockés les zip téléchargés en arrière-plan avant
  bascule au lancement suivant — **commun** à Actualise et à toutes les
  applications cibles gérées par cette installation, cohérent avec le
  fait qu'il n'existe plus qu'une seule installation d'Actualise à
  gérer (voir « Configuration portable »).
- `topic_ntfy` (dans `config_<nom_app>.json`) : topic ntfy dédié à ce
  programme, cohérent avec la décision actée « un topic ntfy dédié par
  programme géré » (voir « Décisions actées »). **Cas particulier
  Scrabble** : pour ce projet spécifiquement, `topic_ntfy` réutilise le
  topic déjà existant des notifications d'issues fermées de
  Bridge_Agent pour Scrabble — pas de topic dédié séparé créé, car seul
  Alain est abonné aux deux flux et le préfixe `"MAJ - "` (voir
  « Décisions actées ») suffit à distinguer visuellement les
  notifications d'Actualise des notifications de clôture d'issue dans
  le même flux. Le principe général « un topic ntfy dédié par programme
  géré » reste la règle par défaut pour de futurs projets ayant un
  public destinataire différent (ex. un autre utilisateur final
  abonné) ; Scrabble est un cas particulier documenté comme tel, pas un
  changement de règle générale.

`repertoire_installation` reste un chemin propre à l'application cible
(ex. `C:\Scrabble\`), indépendant du dossier d'Actualise lui-même
(ex. `C:\Actualise\`) — équivalent portable pour Linux (ex.
`~/.config/actualise/` ou variable d'environnement) ; `zone_attente`,
elle, est désormais toujours un sous-dossier du dossier de
configuration **partagé** d'Actualise (voir « Configuration portable »
ci-dessous), plus jamais un sous-dossier d'une installation propre à
une application cible.

## Configuration portable

**Modèle actuel : instance unique partagée.** Actualise n'est plus
installé une fois par application cible : une **seule** installation
d'Actualise (`Actualise.exe`, son dossier `_internal\`, et
`ActualiseUI.exe`), dans un **dossier partagé et fixe**,
`C:\Actualise\`, gère toutes les applications cibles présentes sur la
machine (ex. Scrabble **et** Rummikub à la fois). Chaque application
cible sait laquelle elle est en passant l'argument obligatoire
`--config <nom>` (ex. `--config scrabble`) à `Actualise.exe`, qui
détermine le nom du fichier `config_<nom>.json` à charger (voir
« Contenu des fichiers de configuration » ci-dessus) — c'est ce
fichier de configuration par application, et non plus un dossier
d'installation séparé, qui isole les applications cibles les unes des
autres.

Techniquement, `config.chemin_config_portable()` résout ce dossier **au
runtime, relativement à l'emplacement de l'exécutable `Actualise.exe`
lui-même** : le dossier qui le contient, obtenu via `sys.executable` en
mode PyInstaller figé (`sys.frozen`) — ce mécanisme de résolution n'a
**pas changé** depuis la conception initiale (issue #4). Ce qui a
changé, c'est la **convention de déploiement** : `Actualise.exe`
n'étant plus installé qu'une seule fois, à un emplacement fixe
(`C:\Actualise\`, imposé par le setup dédié — voir « Intégration avec
le setup.exe d'une application cible »), cette résolution relative
pointe désormais systématiquement vers ce même dossier partagé, quelle
que soit l'application cible qui a lancé Actualise. En mode script non
figé (développement/tests), repli sur `%SYSTEMDRIVE%\Actualise\`.

Sous Linux, le comportement reste inchangé (`~/.config/actualise/` ou
variable d'environnement `ACTUALISE_CONFIG_DIR`) : l'exécutable Linux
n'étant pas installé par un setup Windows par application, la
problématique de collision multi-installations ne s'y pose pas de la
même façon.

Voir « Points de vigilance connus » pour l'historique du modèle
intermédiaire « instances séparées » (un dossier Actualise par
application cible, ex. `C:\Actualise_Scrabble\`) qui a précédé ce
modèle et la raison de son abandon.

## Vérification réseau — timeout strict

Toute requête HTTP de vérification de version (`version.json`, Actualise
ou application cible) doit utiliser un **timeout court (2 à 3
secondes)**. Passé ce délai, la vérification est traitée comme un échec
réseau : comportement déjà acté, on se rabat silencieusement sur la
version installée, sans bloquer l'utilisateur (voir « Décisions
actées »).

## Séquence de démarrage — vérification non bloquante

Principe central : **Actualise ne bloque jamais, et ne lance plus
aucune application cible.** Refonte architecturale actée : c'est
désormais l'application cible qui lance Actualise à son propre
démarrage (et non l'inverse) ; Actualise se limite à l'auto-mise-à-jour
et à la vérification/téléchargement en arrière-plan, puis se termine.

1. L'application cible lance Actualise à son démarrage.
2. En parallèle, dans une **tâche de fond** (thread ou process séparé),
   Actualise :
   - vérifie `version.json` d'Actualise et `version.json` de
     l'application cible (deux vérifications indépendantes, chacune
     avec le timeout strict ci-dessus) ;
   - télécharge (depuis les GitHub Releases correspondantes) toute
     nouvelle version trouvée ; **avant** de la placer en zone d'attente
     locale, Actualise calcule le SHA-256 du zip reçu et le compare au
     champ `sha256` annoncé dans le `version.json` correspondant :
     - **correspondance** → le zip est placé en zone d'attente locale,
       bascule prévue au prochain lancement (comportement déjà décrit
       ci-dessus) ;
     - **non-correspondance** → le téléchargement est rejeté (zip
       corrompu ou tronqué), aucune zone d'attente n'est mise à jour,
       nouvelle tentative au prochain cycle de vérification en
       arrière-plan — même repli que pour un échec réseau : ne jamais
       toucher à l'installation existante ;
   - si une nouvelle version a été téléchargée **et validée**, envoie une
     **notification ntfy informative** (mise à jour prête, effective au
     prochain lancement).

**Cycle de vie du processus Actualise.** Actualise ne lance plus
l'application cible et n'a donc plus aucun lien avec son cycle de vie :
c'est elle qui le lance, à son propre démarrage. Une fois démarré,
Actualise attend uniquement la fin de sa propre **tâche de fond**
(étape 2 ci-dessus), qui va jusqu'au bout de son cycle (vérification
des deux `version.json`, téléchargement et validation SHA-256 si
nécessaire, notification ntfy éventuelle). Dès que cette tâche de fond
se termine, **Actualise se termine à son tour** — que l'application
cible tourne encore ou se soit déjà fermée entre-temps n'a aucune
incidence. Actualise n'est donc pas un processus permanent : c'est un
aller-retour ponctuel déclenché à chaque démarrage de l'application
cible, qui effectue son travail de vérification/téléchargement en
arrière-plan puis se ferme, sans attendre une action de l'utilisateur.

3. Au **lancement suivant** (prochain démarrage d'Actualise, déclenché
   par un nouveau lancement de l'application cible), avant toute autre
   chose, Actualise applique les mises à jour mises en attente. Pour
   chaque mise à jour en attente (Actualise ou application cible), la
   bascule comprend :
   1. **extraction du zip** téléchargé dans le dossier d'installation
      (écrase les fichiers existants de même nom, ajoute les nouveaux) ;
   2. **application du manifeste** : suppression des fichiers listés
      dans `supprimer` (voir « Manifeste de mise à jour »).

   Le détail selon qu'il s'agit d'Actualise lui-même ou de l'application
   cible :
   - si une nouvelle version d'Actualise est en attente, ces deux
     étapes sont suivies d'un relancement d'Actualise comme **2ème
     instance** de lui-même (la version fraîchement installée) avec le
     **marqueur explicite** parent → enfant décrit ci-dessous, avant de
     terminer le parent ; ces opérations restent locales (extraction de
     zip, suppressions ciblées), donc quasi instantanées — elles ne
     réintroduisent pas d'attente réseau perceptible ;
   - si une nouvelle version de l'application cible est en attente, ces
     deux étapes suffisent : Actualise n'a plus rien à lancer ensuite,
     l'application cible tourne déjà dans sa version fraîchement mise à
     jour dès son prochain démarrage.

**Choix écarté : liste de fichiers attendus post-extraction.** Une
vérification de type « liste des fichiers attendus après extraction du
zip » a été envisagée puis écartée : sa couverture est jugée redondante
une fois le SHA-256 du zip validé (le contenu de l'archive est déjà
garanti intègre avant extraction). Une extraction incomplète malgré un
zip validé relèverait d'un problème d'environnement local (disque
plein, permissions insuffisantes), détectable par une simple
vérification d'erreur d'extraction plutôt que par une liste de fichiers
à maintenir en parallèle du manifeste.

**Conséquence assumée** : dans tous les cas (réseau bon, lent ou coupé),
l'utilisateur ne perçoit **aucun délai** au lancement. Le compromis en
contrepartie est qu'une mise à jour n'est **jamais appliquée
immédiatement** : elle est toujours détectée en arrière-plan pendant un
lancement et n'est effective qu'au lancement suivant.

## Nommage versionné des zips en zone d'attente

Convention de nommage dans `zone_attente` : `<préfixe>_<build>.zip` (ex.
`actualise_48.zip`, `scrabble_112.zip`). Le préfixe identifie à qui
appartient le zip (`actualise`, ou le nom de l'application cible tel
que défini dans `config_<nom_app>.json`) ; le numéro de build permet la
comparaison directe avec le `build_installe` correspondant (voir
« Contenu des fichiers de configuration ») sans avoir à ouvrir
le zip ni consulter un fichier séparé.

Comportement au démarrage, **avant bascule** (étape 3 de la séquence
ci-dessus) : pour chaque préfixe connu (`actualise`, nom de
l'application cible), si un fichier `<préfixe>_<build>.zip` existe dans
`zone_attente` :

- si `build` > `build_installe` correspondant → mise à jour valide,
  bascule appliquée (extraction + manifeste, voir étape 3 ci-dessus),
  puis le zip est **supprimé après succès** de la bascule ;
- si `build` ≤ `build_installe` correspondant → résidu obsolète (déjà
  appliqué lors d'un cycle précédent, ou périmé pour toute autre
  raison) → le zip est **supprimé sans être appliqué**, sans bloquer le
  démarrage.

**Cas limite : plusieurs zips du même préfixe présents simultanément**
(ex. `scrabble_47.zip` et `scrabble_48.zip` coexistant dans
`zone_attente`). Ce cas peut survenir légitimement si la tâche de fond
télécharge une nouvelle version avant que la précédente n'ait été
appliquée (l'utilisateur n'a pas relancé l'application entre les deux
cycles de vérification). Comportement retenu : parmi les fichiers
`<préfixe>_<build>.zip` d'un même préfixe, seul celui au **build le
plus élevé** est considéré et éventuellement appliqué (selon la
comparaison `build` > `build_installe` ci-dessus) ; tous les autres
sont **supprimés sans être appliqués**, quelle que soit leur valeur de
`build` — même logique que pour un unique zip obsolète décrite
ci-dessus, un build inférieur au maximum présent étant nécessairement
un résidu dépassé par une version plus récente déjà téléchargée.

Ce mécanisme remplit une double fonction : marqueur d'appartenance
(quel préfixe identifie le zip) et garde-fou contre un zip laissé
indéfiniment dans la zone d'attente — un nettoyage automatique des
résidus obsolètes a lieu à chaque démarrage, complémentaire au
garde-fou par marqueur décrit ci-dessous (« Garde-fou anti-boucle
infinie »).

## Garde-fou anti-boucle infinie

Le garde-fou par marqueur reste nécessaire pour l'auto-mise-à-jour
d'Actualise, mais s'inscrit désormais dans le flux non bloquant
ci-dessus : le relancement parent → enfant n'intervient que pour
**appliquer une mise à jour déjà téléchargée** (bascule locale rapide),
jamais pour attendre une vérification réseau en tout début d'exécution.

Quand une instance d'Actualise lance une 2ème instance (la nouvelle
version, après bascule), elle lui transmet un **marqueur explicite**
signalant qu'il s'agit d'un enfant : variable d'environnement (ex.
`ACTUALISE_CHILD=1`) ou argument de ligne de commande (ex. `--child`),
au choix de l'implémentation. **Si ce marqueur est présent à son
démarrage, l'instance saute inconditionnellement toute bascule
d'auto-mise-à-jour supplémentaire — quoi que dise l'état local — et
passe directement à l'étape 2 de la séquence de démarrage (vérification
et téléchargement en arrière-plan).**

Ce marqueur est portable Linux/Windows et indépendant de l'état des PID
au runtime (pas de lecture du parent, pas de dépendance à `psutil` ni au
nom du processus parent — évite notamment la troncature à 15 caractères
de `/proc/<pid>/comm` sous Linux). Il élimine la boucle par construction
(profondeur maximale 2, aucune 3ème instance ne peut jamais se lancer)
sans nécessiter de compteur ni d'état persistant à gérer.

**Point de vigilance pour l'implémentation** :

- Le parent doit **attendre** la fin de l'enfant (`Popen.wait()` ou
  équivalent) plutôt que l'enfant ne tue le parent explicitement. Cela
  garde une séquence de terminaison simple et déterministe.

**Bascule sécurisée par dossier temporaire + renommage (implémenté).**
Un incident réel en production a confirmé le risque documenté
ci-dessus : `appliquer_mises_a_jour_en_attente` tentait d'extraire
directement le zip d'Actualise dans son propre dossier d'installation
(`repertoire_installation`, celui de l'exécutable en cours
d'exécution), ce qui échoue sous Windows avec `PermissionError [Errno
13]` — un `.exe` en cours d'exécution ne peut pas être réécrit en
place, seulement renommé. Ce point ne concernait que la mise à jour
d'Actualise lui-même (`prefixe == "actualise"`) : l'application cible
n'a pas son exécutable en cours d'exécution au moment de la bascule,
donc son extraction directe reste inchangée et sans risque.

Pour Actualise lui-même, la bascule suit désormais ce mécanisme :

1. Extraction du zip dans un **dossier temporaire distinct**, créé sous
   `repertoire_installation` (`<repertoire_installation>/maj_temp_*/`,
   via `tempfile.TemporaryDirectory`) — jamais directement dans
   `repertoire_installation`.
2. **Bascule par renommage** fichier à fichier (`os.replace`) du
   contenu de ce dossier temporaire vers `repertoire_installation` :
   chaque fichier (y compris l'exécutable `Actualise.exe` lui-même)
   est renommé par-dessus l'ancien, jamais réécrit en place pendant
   qu'il tourne.
3. Le manifeste (`manifest.json`) est appliqué **après** cette
   bascule, directement sur `repertoire_installation` — et non sur le
   dossier temporaire — car `manifest["supprimer"]` cible des fichiers
   obsolètes de l'installation déjà en place, pas nécessairement
   présents dans le zip fraîchement extrait ; l'appliquer au dossier
   temporaire n'aurait donc aucun effet sur ces résidus.
4. Le dossier temporaire est automatiquement nettoyé (context manager
   `TemporaryDirectory`) une fois la bascule terminée (succès ou
   échec).
5. **Si le renommage échoue à nouveau** (ex. fichier encore verrouillé,
   `OSError`) : erreur logguée clairement, zip source **conservé** en
   zone d'attente pour permettre une nouvelle tentative au lancement
   suivant, sans faire planter `main()` — traitement cohérent avec les
   autres cas limites déjà en place (manifeste absent, zip corrompu).

## ActualiseUI.exe — dialogue de mise à jour côté utilisateur final

Module ajouté (issue #36) en complément de la bascule silencieuse
décrite ci-dessus, pour le même problème de fond (le verrou Windows sur
`_internal\`/`Actualise.exe` pendant qu'Actualise tourne, voir
« Garde-fou anti-boucle infinie ») mais en donnant cette fois la main à
l'utilisateur final plutôt qu'en l'appliquant silencieusement. C'est un
**exécutable séparé**,
`ActualiseUI.exe` (`actualise_ui.py`, compilé en `--onefile` via
`actualise_ui.spec`), jamais importé par `actualise.py` : une petite
fenêtre tkinter (« Mettre à jour » / « Plus tard »), sans dépendance
externe, dont le seul rôle est de présenter le choix à l'utilisateur
final et de déclencher un `.bat` généré par Actualise.

Déroulé :

1. Dès que la tâche de fond (« Séquence de démarrage », étape 2) détecte
   et télécharge une nouvelle version d'**Actualise lui-même**, elle
   génère immédiatement, en plus du zip placé en zone d'attente :
   - `updater.bat`, dans le dossier partagé d'Actualise
     (`C:\Actualise\`) — script qui effectue la bascule réelle
     (renommage de `_internal\`/`Actualise.exe` en `.old`, extraction du
     zip, nettoyage) ;
   - `actualise_update.flag`, un JSON déposé dans le
     `repertoire_installation` de **l'application cible** (pas dans le
     dossier d'Actualise), contenant les chemins vers `ActualiseUI.exe`
     et vers `updater.bat`.
2. L'application cible (voir INTEGRATION.md, §6, pour le code exact à
   intégrer une fois pour toutes) détecte ce flag à son propre
   démarrage et lance `ActualiseUI.exe --bat ... --flag ... --relancer
   <son propre exécutable>`, qui affiche la fenêtre de choix.
   - **« Mettre à jour »** : supprime le flag, lance `updater.bat` (qui
     relance l'application cible une fois la bascule terminée, via
     `--relancer`), ferme la fenêtre.
   - **« Plus tard »** : ferme simplement la fenêtre, flag conservé —
     le choix sera reproposé au prochain démarrage.
3. À la **fermeture** de la fenêtre principale de l'application cible,
   si le flag existe encore (mise à jour jamais validée via la
   fenêtre), l'application cible lance directement `updater.bat` (sans
   fenêtre, sans demander confirmation) avant de se fermer. Ceci
   garantit que la mise à jour d'Actualise finit **toujours** par
   s'appliquer — au plus tard à la prochaine fermeture normale de
   l'application cible — même si l'utilisateur ignore systématiquement
   la fenêtre de choix.
4. Tant que ce flag existe, `appliquer_mises_a_jour_en_attente` (étape
   3 de la « Séquence de démarrage ») **saute** la bascule silencieuse
   par renommage pour Actualise : `ActualiseUI.exe`/`updater.bat` a
   alors la main exclusive, pour éviter une double bascule concurrente.
   La bascule silencieuse par renommage (garde-fou anti-boucle
   infinie ci-dessus) reste le mécanisme de **repli** : si le flag/bat
   n'a pas pu être généré (`OSError`), Actualise applique la mise à
   jour lui-même, sans interface, comme avant l'introduction
   d'`ActualiseUI.exe`.

Ce mécanisme concerne **exclusivement** la mise à jour d'Actualise
lui-même : la mise à jour d'une application cible n'a jamais eu besoin
de ce contournement (son exécutable n'est pas en cours d'exécution au
moment de la bascule, voir « Garde-fou anti-boucle infinie »).

## Intégration avec le setup.exe d'une application cible

Deux setups distincts coexistent désormais, avec des responsabilités
disjointes (issue #44) — voir aussi INTEGRATION.md pour le guide
pratique d'intégration complet, à jour sur ce modèle :

1. **`Actualise-Setup.exe`** (`installeur/actualise.iss`) — installeur
   dédié à Actualise lui-même, indépendant de toute application cible.
   Il installe l'instance **partagée** dans un dossier **fixe et non
   modifiable par l'utilisateur** (`DefaultDirName=C:\Actualise`,
   `DisableDirPage=yes`), avec `PrivilegesRequired=admin` (`C:\` racine
   du disque système, inaccessible en écriture aux utilisateurs
   standards ; incident réel documenté avec `PrivilegesRequired=lowest`
   — voir INTEGRATION.md). Il dépose les trois éléments constitutifs
   d'Actualise :
   - `Actualise.exe` ;
   - `_internal\` (dossier complet, jamais l'exe seul — un `_internal\`
     manquant provoque `Failed to load Python DLL`) ;
   - `ActualiseUI.exe` (voir « ActualiseUI.exe » ci-dessus).

   À l'installation (`ssPostInstall`), il crée `config_actualise.json`
   **uniquement s'il n'existe pas déjà** : ce fichier étant partagé
   entre toutes les applications cibles, l'écraser ferait perdre le
   `build_installe`/`zone_attente` déjà à jour d'une installation
   précédente. À la désinstallation, il supprime le dossier
   `C:\Actualise\` **seulement si** aucun `config_<nom>.json` d'une
   autre application cible n'y subsiste (recherche par motif
   `config_*.json`, `config_actualise.json` exclu) — sinon il
   désinstallerait Actualise sous des applications qui en dépendent
   encore. Pas de raccourci créé par ce setup : Actualise n'est jamais
   lancé directement par l'utilisateur (voir la décision actée « le
   raccourci ne doit jamais pointer directement vers l'application
   cible », qui reste — sous une forme adaptée — le raccourci pointe
   toujours vers `Actualise.exe`, jamais vers l'application cible).

2. **Le setup.exe de chaque application cible** (ex. Scrabble,
   Rummikub) — **ne déploie plus** `Actualise.exe`/`_internal\`/
   `ActualiseUI.exe` lui-même (ancien comportement, avant issue #44, où
   chaque setup cible embarquait et réinstallait sa propre copie
   d'Actualise). Son rôle se limite désormais à :
   - déposer son propre `config_<nom>.json` dans `C:\Actualise\`
     (jamais `config_actualise.json`, propriété exclusive du setup
     Actualise) ;
   - créer le raccourci Bureau/menu Démarrer pointant vers
     `C:\Actualise\Actualise.exe --config <nom>` — jamais directement
     vers l'exécutable de l'application cible (décision actée dès le
     « Principe de fonctionnement ») ;
   - déployer son propre fichier `.ico` et l'utiliser à la fois pour le
     champ `IconFilename` du raccourci créé (qui pointe vers
     `Actualise.exe` mais affiche l'icône de l'application cible) et
     pour le champ `icone` de `config_<nom>.json` — même chemin dans
     les deux cas, pour cohérence documentée (voir « Contenu des
     fichiers de configuration »).

   Ce découplage préserve la réutilisabilité d'Actualise pour de
   futures applications cibles et sépare le cycle de vie des
   installations : désinstaller une application cible ne désinstalle
   pas nécessairement Actualise, qui continue de gérer les autres
   programmes présents sur la machine (voir point 1 ci-dessus).

Historique : voir « Points de vigilance connus » pour le détail complet
du passage du modèle « instances séparées » (une installation
d'Actualise par application cible, chacune avec son propre `config.json`
et son propre dossier) à ce modèle à deux setups distincts.

## Décisions actées

| Point | Décision |
|---|---|
| Déclenchement de version "officielle" | Alain décide manuellement quand publier une version (via les Releases GitHub, avec tag de version) — pas à chaque commit |
| Comportement hors-ligne / échec réseau | Se rabat silencieusement sur le lancement de la version déjà installée, sans bloquer l'utilisateur final |
| Raccourci utilisateur | Pointe vers Actualise, jamais directement vers l'application cible |
| Configuration | Répertoire dédié type `C:\Actualise\` avec un fichier `config.json` reprenant : version actuelle de l'exe cible, dépôt GitHub cible, répertoire d'installation cible, et autres éléments à définir. Prévoir un chemin **portable** pour les tests/usage Linux (ex. `~/.config/actualise/` ou une variable d'environnement) en plus de `C:\Actualise\`, pour ne pas entamer la réutilisabilité Linux visée par le projet |
| Notifications | Un topic ntfy dédié par programme géré (règle par défaut) ; notification informative envoyée quand une mise à jour a été téléchargée en arrière-plan (effective au prochain lancement), message préfixé par `"MAJ - "` pour se distinguer visuellement d'autres types de notifications pouvant partager le même topic ; **cas particulier Scrabble** : réutilise le topic existant des notifications d'issues fermées Bridge_Agent du projet Scrabble plutôt qu'un topic dédié séparé, car seul Alain est abonné aux deux flux — voir « Contenu des fichiers de configuration » |
| Format de version | `version.json` avec entier incrémental `build` (ex. `{"build": 47}`), comparaison `>` entre entiers — pas de semver ni de comparaison de chaînes brute (piège "9" > "10" lexicographique) |
| Fichiers `version.json` | Deux fichiers distincts et indépendants : un dans le dépôt Actualise, un dans le dépôt de chaque application cible (URL construite depuis `config_<nom_app>.json`) |
| Distribution des binaires | Assets de GitHub Releases (URL stable `releases/download/<tag>/<fichier>`), pas commités dans l'historique ; **un seul asset par tag, sous forme d'archive zip** contenant tous les fichiers de la version (exécutable, données, DLL) et le manifeste ; **nom d'asset fixe `<préfixe>.zip`** (ex. `actualise.zip`, `scrabble.zip`), sans numéro de version dans le nom du fichier — chaque nouvelle Release re-uploade un asset de ce même nom ; **tag de Release au format `v<build>`** (ex. `v48`) ; diff binaire écarté (gain marginal, binaires PyInstaller recompilés quasi-intégralement à chaque changement) |
| `version.json` (stockage) | Reste un petit fichier commité normalement dans le dépôt, pas un asset de Release |
| Manifeste de mise à jour | `manifest.json` à la racine du zip (`{"build": N, "supprimer": [...]}`) ; `supprimer` est une liste noire optionnelle de chemins à effacer après extraction — fail-safe (un oubli laisse un fichier obsolète, jamais une perte de données) ; script `.bat`/`.sh` exécutable écarté pour portabilité Linux/Windows et sécurité (pas d'exécution de code téléchargé sans supervision) ; **`manifest.json` absent → bloquant** : bascule échoue, non appliquée, zip conservé pour nouvelle tentative ultérieure (zip considéré malformé, pas une absence volontaire de suppression) |
| Timeout réseau | 2 à 3 secondes sur toute requête de vérification de version ; dépassement traité comme échec réseau |
| Séquence de démarrage | Non bloquante : Actualise est désormais lancé par l'application cible à son démarrage (et non l'inverse), il ne lance plus aucune application cible ; vérification et téléchargement en arrière-plan, appliqués au lancement suivant ; notification ntfy si mise à jour prête |
| Vérification SHA-256 du zip | `version.json` porte un champ `sha256` du zip complet publié ; après téléchargement, avant mise en zone d'attente, comparaison du SHA-256 calculé sur le fichier reçu ; non-correspondance → téléchargement rejeté, aucune zone d'attente mise à jour, nouvelle tentative au cycle suivant (même repli que pour un échec réseau) ; liste de fichiers attendus post-extraction écartée (redondante une fois le zip validé, une extraction incomplète relevant d'un problème d'environnement local détectable par vérification d'erreur d'extraction) |
| Bootstrap séparé | Écarté pour l'instant — Actualise reste un exécutable unique qui se met à jour lui-même, avec le garde-fou par marqueur ci-dessus |
| Garde-fou anti-boucle | Marqueur explicite transmis parent → enfant (env `ACTUALISE_CHILD=1` ou arg `--child`), déclenché uniquement lors de la bascule d'une mise à jour déjà téléchargée — voir section dédiée ci-dessus |
| Configuration portable | Dossier résolu **relativement à l'emplacement de l'exécutable `Actualise.exe`** (via `sys.executable` en mode PyInstaller figé, `config.chemin_config_portable()`) — mécanisme de résolution inchangé depuis la conception initiale (issue #4) ; ce qui a changé (issue #44), c'est la convention de déploiement : `Actualise.exe` n'est plus installé qu'une seule fois, dans un dossier fixe et **partagé** (`C:\Actualise\`, imposé par `Actualise-Setup.exe`), donc cette résolution relative pointe désormais systématiquement vers ce même dossier partagé quelle que soit l'application cible qui a lancé Actualise ; équivalent portable sous Linux inchangé (`~/.config/actualise/` ou variable d'environnement `ACTUALISE_CONFIG_DIR`) — voir « Configuration portable » et « Points de vigilance connus » pour l'historique complet |
| Contenu de la configuration | Deux fichiers séparés (issue #35) remplaçant l'ancien `config.json` unique à deux blocs : `config_actualise.json` (un seul exemplaire, **partagé** entre toutes les applications cibles gérées par cette installation — `build_installe`, `depot_github`, `zone_attente` d'Actualise) et `config_<nom_app>.json` (un exemplaire **par application cible** — `nom`, `depot_github`, `build_installe`, `repertoire_installation`, `executable`, `icone` optionnel, `topic_ntfy`) ; sélection du fichier `config_<nom_app>.json` à charger via l'argument obligatoire `--config <nom>` passé à `Actualise.exe` ; `config.charger_config(nom_app)` lit et fusionne les deux fichiers en un seul dict pour le reste d'Actualise — voir « Contenu des fichiers de configuration » |
| Intégration au setup.exe cible | Modèle actuel (issue #44) : **deux setups distincts**. `Actualise-Setup.exe` (installeur InnoSetup dédié, `installeur/actualise.iss`) installe l'instance partagée d'Actualise une seule fois, dans un dossier fixe et non modifiable `C:\Actualise\` (`DisableDirPage=yes`, `PrivilegesRequired=admin`), et crée `config_actualise.json` seulement s'il n'existe pas déjà. Le setup de chaque application cible **ne déploie plus Actualise lui-même** — seulement son `config_<nom>.json`, son raccourci Bureau/menu Démarrer vers `Actualise.exe --config <nom>` (jamais directement vers l'application cible), et son icône `.ico` (même chemin utilisé pour `IconFilename` du raccourci et pour le champ `icone` de `config_<nom>.json`) — voir « Intégration avec le setup.exe d'une application cible » |
| ActualiseUI.exe | Module séparé (issue #36), jamais importé par `actualise.py`, compilé en exécutable indépendant (`actualise_ui.py` → `ActualiseUI.exe`) et déployé uniquement par `Actualise-Setup.exe`. Gère le dialogue de mise à jour d'Actualise côté utilisateur final (fenêtre tkinter « Mettre à jour »/« Plus tard »), en repli sur la bascule silencieuse par renommage si le flag/bat n'a pas pu être généré — voir « ActualiseUI.exe — dialogue de mise à jour côté utilisateur final » |
| Cycle de vie d'Actualise | Actualise ne lance plus l'application cible — c'est elle qui le lance à son démarrage ; Actualise attend uniquement la fin de sa propre tâche de fond (vérification, téléchargement, validation SHA-256, notification ntfy), puis se termine — indépendamment du cycle de vie de l'application cible ; Actualise n'est pas un processus permanent, c'est un aller-retour ponctuel à chaque démarrage de l'application cible |
| Nommage versionné des zips en zone d'attente | `<préfixe>_<build>.zip` (ex. `actualise_48.zip`, `scrabble_112.zip`) — comparaison directe avec `build_installe` sans ouvrir le zip ; au démarrage, résidu avec `build` ≤ `build_installe` correspondant supprimé sans être appliqué (nettoyage automatique, garde-fou contre un zip bloqué indéfiniment en zone d'attente) ; **si plusieurs zips du même préfixe coexistent**, seul celui au build le plus élevé est considéré, les autres supprimés sans être appliqués (même logique que pour un résidu obsolète) — voir « Nommage versionné des zips en zone d'attente » |

## Points de vigilance connus

- **Cache CDN de `version.json`** : servi via `raw.githubusercontent.com`,
  le fichier `version.json` est mis en cache par le CDN GitHub (~5
  minutes). La détection d'une nouvelle version peut donc être retardée
  d'autant après une publication. Jugé acceptable pour l'usage visé (pas
  de mise à jour urgente à la minute près), mais documenté ici pour
  mémoire — une éventuelle parade (paramètre anti-cache, endpoint API
  GitHub, ou tag Release) reste ouverte si le délai devenait gênant.
- **Incident à l'origine de la « Configuration portable » relative à
  l'exécutable** : l'installation simultanée de plusieurs applications
  cibles sur la même machine (ex. Scrabble et Rummikub) a révélé qu'un
  chemin de configuration fixe (`C:\Actualise\`) faisait écraser
  silencieusement le `config.json` d'une première installation par la
  seconde, cette dernière lui faisant perdre la gestion de mise à jour
  de sa propre application cible — sans erreur visible, jusqu'à
  constater qu'une des deux applications ne se mettait plus à jour.
  Corrigé en résolvant le dossier de configuration relativement à
  l'emplacement de l'exécutable `Actualise.exe` plutôt qu'un chemin
  codé en dur (voir « Configuration portable »). Ce mécanisme de
  résolution reste inchangé aujourd'hui ; voir le point suivant pour ce
  qui a changé depuis dans la façon dont il est exploité.
- **Passage du modèle « instances séparées » au modèle « instance
  unique partagée »** (issues #27, #35, #36, #44) : la parade retenue
  pour l'incident ci-dessus consistait à installer une copie complète
  et indépendante d'Actualise **par application cible**, chacune dans
  son propre dossier (convention suggérée `C:\Actualise_<NomApplication>\`,
  ex. `C:\Actualise_Scrabble\`, `C:\Actualise_Rummikub\`), avec son
  propre `config.json` complet — modèle documenté dans une révision
  précédente de cette section. Ce modèle **a depuis été abandonné** au
  profit d'un refactor plus profond : une **instance unique partagée**
  d'Actualise (`C:\Actualise\`), avec un fichier de configuration
  **distinct par application cible** (`config_<nom>.json`) plutôt
  qu'une installation distincte par application cible. Le mécanisme de
  résolution relative à l'exécutable (`sys.executable`) qui avait rendu
  possible le modèle « instances séparées » n'a pas changé ; ce qui
  change, c'est qu'il n'y a désormais plus qu'un seul `Actualise.exe`
  installé sur la machine à résoudre, puisqu'une seule installation
  existe pour toutes les applications cibles.

  Ce refactor a été mené en plusieurs étapes distinctes, chacune
  correspondant à une issue séparée : séparation de `config.json` en
  `config_actualise.json` (partagé) et `config_<nom>.json` (par
  application), avec argument `--config <nom>` obligatoire pour
  sélectionner lequel charger (issue #35) ; ajout d'`ActualiseUI.exe`,
  module séparé gérant le dialogue de mise à jour côté utilisateur
  final et contournant le verrou Windows sur `_internal\` pendant
  l'exécution d'Actualise (issue #36) ; ajout d'`Actualise-Setup.exe`,
  installeur InnoSetup dédié et indépendant des setups des applications
  cibles, qui installe l'instance partagée une seule fois pour toutes
  (issue #44). Avantage par rapport au modèle « instances séparées » :
  une seule copie d'Actualise à maintenir et mettre à jour sur la
  machine, plutôt qu'une par application cible avec son propre cycle de
  mise à jour indépendant. Contrepartie : réintroduction d'un état
  partagé (`config_actualise.json`), dont la collision initiale (objet
  du point précédent) est cette fois évitée non plus par l'isolement
  des dossiers d'installation, mais par la logique applicative
  d'`Actualise-Setup.exe` (ne jamais écraser `config_actualise.json`
  s'il existe déjà) combinée à la séparation stricte des fichiers de
  configuration par application cible.
