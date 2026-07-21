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

À son démarrage, Actualise vérifie le nom de son processus parent (PPID,
via `psutil` ou équivalent portable Linux/Windows). **Si ce parent est
lui-même un processus `Actualise`, l'instance saute inconditionnellement
l'étape d'auto-mise-à-jour — quoi que dise `version.json` — et passe
directement à la gestion de l'application cible.**

Ce mécanisme élimine la boucle par construction (profondeur maximale 2,
aucune 3ème instance ne peut jamais se lancer) sans nécessiter de
compteur ni d'état persistant à gérer.

**Résidu de fragilité assumé** : une fenêtre théorique très étroite existe
si le parent plantait et que son PID était réutilisé par un autre
processus avant la vérification — dans ce cas rare, Actualise pourrait
retenter une mise à jour une fois de trop. Risque jugé acceptable (pas de
boucle indéfinie possible, juste une tentative ponctuelle supplémentaire
dans un cas limite).

**Point de vigilance pour l'implémentation** : Actualise 1 doit rester
vivant jusqu'à ce qu'Actualise 2 le termine explicitement (plutôt que de
quitter immédiatement après l'avoir lancé), afin de garantir que le
parent est bien vivant au moment où l'enfant vérifie son PPID — évite le
risque de réattachement ("reparenting") à `init`/PID 1 sur Linux avant la
vérification.

## Décisions actées

| Point | Décision |
|---|---|
| Déclenchement de version "officielle" | Alain décide manuellement quand publier une version (probablement via les Releases GitHub, avec tag de version) — pas à chaque commit |
| Comportement hors-ligne / échec réseau | Se rabat silencieusement sur le lancement de la version déjà installée, sans bloquer l'utilisateur final |
| Raccourci utilisateur | Pointe vers Actualise, jamais directement vers l'application cible |
| Configuration | Répertoire dédié type `C:\Actualise\` avec un fichier `config.json` reprenant : version actuelle de l'exe cible, dépôt GitHub cible, répertoire d'installation cible, et autres éléments à définir |
| Notifications | Un topic ntfy dédié par programme géré |
| Détection de version | Fichier `version.json` sur le dépôt GitHub, comparaison distante vs locale — portable Linux/Windows |
| Bootstrap séparé | Écarté pour l'instant — Actualise reste un exécutable unique qui se met à jour lui-même, avec le garde-fou PPID ci-dessus |
| Garde-fou anti-boucle | Vérification du nom du parent via PPID (voir section dédiée ci-dessus) |

## Points encore ouverts

- Mécanisme exact de comparaison de version dans `version.json` (numéro
  simple, semver, hash, autre).
- Format exact du téléchargement/remplacement des fichiers (zip complet,
  diff, autre).
- Contenu détaillé de `config.json` au-delà de "version actuelle, dépôt
  GitHub, répertoire".
- Interaction avec le futur `setup.exe` de Scrabble.
