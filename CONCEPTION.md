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
  informations du `config.json` local (dépôt GitHub cible).

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

## Vérification réseau — timeout strict

Toute requête HTTP de vérification de version (`version.json`, Actualise
ou application cible) doit utiliser un **timeout court (2 à 3
secondes)**. Passé ce délai, la vérification est traitée comme un échec
réseau : comportement déjà acté, on se rabat silencieusement sur la
version installée, sans bloquer l'utilisateur (voir « Décisions
actées »).

## Séquence de démarrage — vérification non bloquante

Principe central : **le lancement de l'application cible n'attend
jamais le réseau.**

1. Lancement d'Actualise.
2. Actualise **lance immédiatement** l'application cible dans sa version
   actuellement installée, sans attendre aucune vérification.
3. En parallèle, dans une **tâche de fond** (thread ou process séparé),
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
4. Au **lancement suivant**, avant de relancer l'application cible,
   Actualise applique les mises à jour mises en attente. Pour chaque
   mise à jour en attente (Actualise ou application cible), la bascule
   comprend désormais trois étapes, dans l'ordre :
   1. **extraction du zip** téléchargé dans le dossier d'installation
      (écrase les fichiers existants de même nom, ajoute les nouveaux) ;
   2. **application du manifeste** : suppression des fichiers listés
      dans `supprimer` (voir « Manifeste de mise à jour ») ;
   3. **lancement de l'application** fraîchement mise à jour.

   Le détail selon qu'il s'agit d'Actualise lui-même ou de l'application
   cible :
   - si une nouvelle version d'Actualise est en attente, ces trois
     étapes sont suivies d'un relancement d'Actualise comme **2ème
     instance** de lui-même (la version fraîchement installée) avec le
     **marqueur explicite** parent → enfant décrit ci-dessous, avant de
     terminer le parent ; ces opérations restent locales (extraction de
     zip, suppressions ciblées), donc quasi instantanées — elles ne
     réintroduisent pas d'attente réseau perceptible ;
   - si une nouvelle version de l'application cible est en attente, ces
     trois étapes sont appliquées avant le lancement (étape 2) de ce
     lancement.

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
passe directement à l'étape 2 de la séquence de démarrage (lancement
immédiat de l'application cible).**

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
- La nouvelle version d'Actualise doit être téléchargée/écrite sous un
  **nom ou chemin temporaire distinct** de l'exécutable en cours
  d'exécution, puis basculée par renommage (`rename` /
  `MoveFileEx`) une fois l'ancien process terminé. Un `.exe` en cours
  d'exécution ne peut pas être réécrit en place sous Windows (seulement
  renommé) : écrire à côté puis renommer évite tout verrouillage de
  fichier.

## Décisions actées

| Point | Décision |
|---|---|
| Déclenchement de version "officielle" | Alain décide manuellement quand publier une version (via les Releases GitHub, avec tag de version) — pas à chaque commit |
| Comportement hors-ligne / échec réseau | Se rabat silencieusement sur le lancement de la version déjà installée, sans bloquer l'utilisateur final |
| Raccourci utilisateur | Pointe vers Actualise, jamais directement vers l'application cible |
| Configuration | Répertoire dédié type `C:\Actualise\` avec un fichier `config.json` reprenant : version actuelle de l'exe cible, dépôt GitHub cible, répertoire d'installation cible, et autres éléments à définir. Prévoir un chemin **portable** pour les tests/usage Linux (ex. `~/.config/actualise/` ou une variable d'environnement) en plus de `C:\Actualise\`, pour ne pas entamer la réutilisabilité Linux visée par le projet |
| Notifications | Un topic ntfy dédié par programme géré ; notification informative envoyée quand une mise à jour a été téléchargée en arrière-plan (effective au prochain lancement) |
| Format de version | `version.json` avec entier incrémental `build` (ex. `{"build": 47}`), comparaison `>` entre entiers — pas de semver ni de comparaison de chaînes brute (piège "9" > "10" lexicographique) |
| Fichiers `version.json` | Deux fichiers distincts et indépendants : un dans le dépôt Actualise, un dans le dépôt de chaque application cible (URL construite depuis `config.json`) |
| Distribution des binaires | Assets de GitHub Releases (URL stable `releases/download/<tag>/<fichier>`), pas commités dans l'historique ; **un seul asset par tag, sous forme d'archive zip** contenant tous les fichiers de la version (exécutable, données, DLL) et le manifeste ; diff binaire écarté (gain marginal, binaires PyInstaller recompilés quasi-intégralement à chaque changement) |
| `version.json` (stockage) | Reste un petit fichier commité normalement dans le dépôt, pas un asset de Release |
| Manifeste de mise à jour | `manifest.json` à la racine du zip (`{"build": N, "supprimer": [...]}`) ; `supprimer` est une liste noire optionnelle de chemins à effacer après extraction — fail-safe (un oubli laisse un fichier obsolète, jamais une perte de données) ; script `.bat`/`.sh` exécutable écarté pour portabilité Linux/Windows et sécurité (pas d'exécution de code téléchargé sans supervision) |
| Timeout réseau | 2 à 3 secondes sur toute requête de vérification de version ; dépassement traité comme échec réseau |
| Séquence de démarrage | Non bloquante : lancement immédiat de l'application cible dans sa version installée ; vérification et téléchargement en arrière-plan, appliqués au lancement suivant ; notification ntfy si mise à jour prête |
| Vérification SHA-256 du zip | `version.json` porte un champ `sha256` du zip complet publié ; après téléchargement, avant mise en zone d'attente, comparaison du SHA-256 calculé sur le fichier reçu ; non-correspondance → téléchargement rejeté, aucune zone d'attente mise à jour, nouvelle tentative au cycle suivant (même repli que pour un échec réseau) ; liste de fichiers attendus post-extraction écartée (redondante une fois le zip validé, une extraction incomplète relevant d'un problème d'environnement local détectable par vérification d'erreur d'extraction) |
| Bootstrap séparé | Écarté pour l'instant — Actualise reste un exécutable unique qui se met à jour lui-même, avec le garde-fou par marqueur ci-dessus |
| Garde-fou anti-boucle | Marqueur explicite transmis parent → enfant (env `ACTUALISE_CHILD=1` ou arg `--child`), déclenché uniquement lors de la bascule d'une mise à jour déjà téléchargée — voir section dédiée ci-dessus |
| Configuration portable | `C:\Actualise\` sous Windows, équivalent portable sous Linux (ex. `~/.config/actualise/` ou variable d'environnement) pour préserver la réutilisabilité Linux |

## Points encore ouverts

- Contenu détaillé de `config.json` au-delà de "version actuelle, dépôt
  GitHub, répertoire".
- Emplacement exact de la zone d'attente locale pour les archives zip
  téléchargées en arrière-plan (Actualise et application cible) avant
  bascule au lancement suivant (le format, lui, est désormais acté :
  zip + `manifest.json`, voir « Manifeste de mise à jour »).
- Interaction avec le futur `setup.exe` de Scrabble.

## Points de vigilance connus

- **Cache CDN de `version.json`** : servi via `raw.githubusercontent.com`,
  le fichier `version.json` est mis en cache par le CDN GitHub (~5
  minutes). La détection d'une nouvelle version peut donc être retardée
  d'autant après une publication. Jugé acceptable pour l'usage visé (pas
  de mise à jour urgente à la minute près), mais documenté ici pour
  mémoire — une éventuelle parade (paramètre anti-cache, endpoint API
  GitHub, ou tag Release) reste ouverte si le délai devenait gênant.
