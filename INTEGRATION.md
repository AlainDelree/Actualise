# Intégration — guide pratique pour une application cible

## 1. Objectif du document

Ce document est un guide **pratique, orienté checklist/action**, destiné
à une conversation Claude qui travaille sur une application cible
(Scrabble, Rummikub, ou un futur projet) et doit l'intégrer avec
Actualise. Il rassemble les points opérationnels et les pièges déjà
rencontrés en production, sous une forme directement actionnable.

Il **complète** [CONCEPTION.md](CONCEPTION.md), qui reste la référence
pour l'architecture complète, le détail de chaque champ et les
justifications des choix de conception. En cas de doute ou de besoin de
détail supplémentaire, se reporter à CONCEPTION.md — ce document ne
duplique pas ce detail.

## 2. Checklist d'intégration pour un nouveau projet cible

- **Dossier d'installation dédié** : `C:\Actualise_<NomApplication>\`
  (ex. `C:\Actualise_Scrabble\`) — **jamais** `C:\Actualise\` seul, sous
  peine de collision entre applications cibles installées sur la même
  machine (voir CONCEPTION.md « Configuration portable » et « Points de
  vigilance connus »).
- **Raccourci** (Bureau/menu Démarrer) pointant vers `Actualise.exe`
  dans ce dossier — **jamais** vers l'exécutable de l'application cible
  directement, sinon la mise à jour ne se déclenche jamais.
- **Icône du raccourci** : déployer un fichier `.ico` propre à
  l'application cible et utiliser **le même chemin** pour :
  - le champ `IconFilename` du raccourci (qui continue de pointer vers
    `Actualise.exe`) ;
  - le champ `icone` du `config.json` généré (voir §3).
- **`config.json` initial complet** généré par le setup, reflétant les
  valeurs réelles de cette installation (voir §3 et §4).
- **Copie intégrale du contenu extrait de `actualise.zip`** par le
  setup : `Actualise.exe` **et** le dossier `_internal\` — jamais l'exe
  seul. Incident réel : `Failed to load Python DLL` au lancement si
  `_internal\` manque.
- Le dépôt de l'application cible doit publier :
  - son propre `version.json` (`{"build": N, "sha256": "..."}`) ;
  - ses Releases GitHub au format `<préfixe>.zip` (asset de nom fixe,
    tag `v<build>`), avec un `manifest.json` inclus à la racine du zip.

  Voir CONCEPTION.md « Distribution des binaires » et « Manifeste de
  mise à jour » pour le détail complet de ce format.

## 3. Format de `config.json` (référence rapide)

```json
{
  "actualise": {
    "build_installe": 3,
    "depot_github": "AlainDelree/Actualise"
  },
  "application_cible": {
    "nom": "Scrabble",
    "depot_github": "AlainDelree/Scrabble",
    "build_installe": 47,
    "repertoire_installation": "C:\\Scrabble\\",
    "executable": "Scrabble.exe",
    "icone": "C:\\Scrabble\\Scrabble.ico"
  },
  "zone_attente": "C:\\Actualise_Scrabble\\attente\\",
  "topic_ntfy": "actualise-scrabble"
}
```

Le détail de chaque champ (rôle exact, portabilité Linux/Windows, cas
particulier de `icone` non lu au runtime, etc.) est documenté dans
CONCEPTION.md « Contenu de `config.json` » — ne pas dupliquer ici.

## 4. Génération de `build_installe` — piège connu

`build_installe` sous le bloc `actualise` doit refléter la **version
réelle d'Actualise embarquée** au moment du build du setup, lue
**dynamiquement** (ex. depuis le `manifest.json` du zip Actualise
téléchargé/embarqué), **jamais une valeur figée en dur** dans le script
de build.

**Incident réel** : un `config.json` généré avec `build_installe: 1`
alors que la v2 d'Actualise était réellement embarquée a provoqué une
boucle de fausse détection de mise à jour (Actualise se croyait en
retard sur lui-même en permanence).

## 5. Bug bootstrap connu (Actualise ≤ v2) — implication permanente

Un Actualise en **v1 ou v2** contient un bug qui l'empêche de
s'auto-mettre-à-jour vers v3 : `PermissionError` lors de la bascule
(l'exécutable en cours d'exécution ne peut pas être réécrit en place).
Corrigé en v3 par la bascule via dossier temporaire + renommage — voir
CONCEPTION.md « Garde-fou anti-boucle infinie » (section « Bascule
sécurisée par dossier temporaire + renommage »).

**Ce cas ne peut pas s'auto-réparer** : une instance encore en v1/v2 ne
peut pas se corriger elle-même en se mettant à jour, puisque le bug est
précisément dans son propre mécanisme de bascule. Toute installation
encore en v1/v2 doit être **réinstallée** avec un setup embarquant
directement v3 ou une version plus récente.

**Contournement de secours** si un utilisateur est bloqué en attendant
une réinstallation : éditer manuellement `build_installe` (bloc
`actualise`) dans son `config.json` vers le numéro déjà présent en zone
d'attente, et supprimer les zips résiduels de `zone_attente`. Ceci
débloque l'usage immédiat (plus de boucle de fausse détection), mais
laisse l'exécutable `Actualise.exe` **physiquement daté** (toujours en
v1/v2) — seule une réinstallation corrige réellement la situation.

Une fois une machine réellement mise à jour vers v3 ou plus récent, les
mises à jour futures fonctionnent normalement : le bug ne concernait que
cette transition précise (v1/v2 → v3), pas le mécanisme de mise à jour
en général.

## 6. Workflow de publication (mode `--publier`)

Le principe déjà en place pour Actualise (documenté dans
`BUILD_WINDOWS_CCW.md`, dépôt bridge_agent) :

- numéro de build **auto-incrémenté** (ou forçable explicitement) ;
- SHA-256 du zip publié **calculé automatiquement** ;
- `version.json` mis à jour et **commit local automatisé** ;
- `git push` et création de la **Release GitHub toujours manuels** (pas
  d'automatisation qui pousserait ou publierait sans validation
  explicite).

**Recommandation** : adopter le même principe pour les scripts de build
des applications cibles — cohérence de workflow entre Actualise et
chaque application cible, et même garde-fou (aucune publication
distante sans validation manuelle).

## 7. Convention ntfy

Le `topic_ntfy` d'une application cible peut être :

- **réutilisé** depuis un topic existant, si pertinent — cas Scrabble :
  réutilisation du topic de clôture d'issue Bridge_Agent déjà existant,
  avec le préfixe `"MAJ - "` sur les messages d'Actualise pour les
  distinguer visuellement des notifications de clôture d'issue dans le
  même flux ;
- ou **dédié**, dans un topic propre à l'application cible (règle par
  défaut pour un public destinataire différent).

Les deux options sont valables, tant que les messages restent
identifiables (préfixe ou topic distinct). Voir CONCEPTION.md « Décisions
actées » (ligne « Notifications ») pour le détail de cette règle.
