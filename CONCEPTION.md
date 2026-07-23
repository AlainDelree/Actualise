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

### Séquence de démarrage

1. Lancement d'Actualise (1ère instance).
2. Actualise vérifie s'il existe une mise à jour de lui-même, via un
   fichier `version.json` hébergé sur son dépôt GitHub (comparaison
   version distante vs version locale — mécanisme portable Linux/Windows,
   sans dépendance à `gh` CLI).
3. Si une mise à jour d'Actualise est trouvée :
   - Téléchargement et installation de la nouvelle version d'Actualise.
   - Lancement d'une 2ème instance d'Actualise (la nouvelle version).
   - Cette 2ème instance vérifie si Actualise est maintenant à jour :
     - Si oui : procède à la vérification/mise à jour de l'application
       cible (ex. Scrabble), puis lance l'application cible.
     - Si non : envoie une notification ntfy, puis lance quand même
       l'application cible (dans sa version actuelle) — pour ne jamais
       bloquer l'utilisateur final.
4. Si aucune mise à jour d'Actualise n'est trouvée à l'étape 2 : passe
   directement à la vérification/mise à jour de l'application cible, puis
   la lance.

## Garde-fou anti-boucle infinie

Quand une instance d'Actualise lance une 2ème instance (la nouvelle
version), elle lui transmet un **marqueur explicite** signalant qu'il
s'agit d'un enfant : variable d'environnement (ex. `ACTUALISE_CHILD=1`)
ou argument de ligne de commande (ex. `--child`), au choix de
l'implémentation. **Si ce marqueur est présent à son démarrage,
l'instance saute inconditionnellement l'étape d'auto-mise-à-jour — quoi
que dise `version.json` — et passe directement à la gestion de
l'application cible.**

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
| Déclenchement de version "officielle" | Alain décide manuellement quand publier une version (probablement via les Releases GitHub, avec tag de version) — pas à chaque commit |
| Comportement hors-ligne / échec réseau | Se rabat silencieusement sur le lancement de la version déjà installée, sans bloquer l'utilisateur final |
| Raccourci utilisateur | Pointe vers Actualise, jamais directement vers l'application cible |
| Configuration | Répertoire dédié type `C:\Actualise\` avec un fichier `config.json` reprenant : version actuelle de l'exe cible, dépôt GitHub cible, répertoire d'installation cible, et autres éléments à définir. Prévoir un chemin **portable** pour les tests/usage Linux (ex. `~/.config/actualise/` ou une variable d'environnement) en plus de `C:\Actualise\`, pour ne pas entamer la réutilisabilité Linux visée par le projet |
| Notifications | Un topic ntfy dédié par programme géré |
| Détection de version | Fichier `version.json` sur le dépôt GitHub, comparaison distante vs locale — portable Linux/Windows |
| Bootstrap séparé | Écarté pour l'instant — Actualise reste un exécutable unique qui se met à jour lui-même, avec le garde-fou par marqueur ci-dessus |
| Garde-fou anti-boucle | Marqueur explicite transmis parent → enfant (env `ACTUALISE_CHILD=1` ou arg `--child`), voir section dédiée ci-dessus |
| Configuration portable | `C:\Actualise\` sous Windows, équivalent portable sous Linux (ex. `~/.config/actualise/` ou variable d'environnement) pour préserver la réutilisabilité Linux |

## Points encore ouverts

- Mécanisme exact de comparaison de version dans `version.json` (numéro
  simple, semver, hash, autre).
- Format exact du téléchargement/remplacement des fichiers (zip complet,
  diff, autre).
- Contenu détaillé de `config.json` au-delà de "version actuelle, dépôt
  GitHub, répertoire".
- Interaction avec le futur `setup.exe` de Scrabble.

## Points de vigilance connus

- **Cache CDN de `version.json`** : servi via `raw.githubusercontent.com`,
  le fichier `version.json` est mis en cache par le CDN GitHub (~5
  minutes). La détection d'une nouvelle version peut donc être retardée
  d'autant après une publication. Jugé acceptable pour l'usage visé (pas
  de mise à jour urgente à la minute près), mais documenté ici pour
  mémoire — une éventuelle parade (paramètre anti-cache, endpoint API
  GitHub, ou tag Release) reste ouverte si le délai devenait gênant.
