# Intégration avec le setup.exe d'une application cible

Deux setups distincts coexistent, avec des responsabilités disjointes —
voir aussi INTEGRATION.md pour le guide pratique d'intégration complet,
à jour sur ce modèle :

1. **`Actualise-Setup.exe`** (`installeur/actualise.iss`) — installeur
   dédié à Actualise lui-même, indépendant de toute application cible.
   Il installe l'instance **partagée** dans un dossier **fixe, sans
   choix laissé à l'utilisateur** (`DefaultDirName=C:\Actualise`,
   `DisableDirPage=yes`), avec `PrivilegesRequired=admin` (requis pour
   que les constantes InnoSetup « tous les utilisateurs » résolvent
   correctement ; incident réel documenté avec
   `PrivilegesRequired=lowest` — voir INTEGRATION.md). Le dossier
   `C:\Actualise\` lui-même n'est protégé par aucune règle de droits
   posée par ce setup : en pratique il reste modifiable en écriture par
   tous les utilisateurs locaux du PC (voir `.audit.json`, SEC-022, pour
   le risque accepté). Il dépose les trois éléments constitutifs
   d'Actualise :
   - `Actualise.exe` ;
   - `_internal\` (dossier complet, jamais l'exe seul — un `_internal\`
     manquant provoque `Failed to load Python DLL`) ;
   - `ActualiseUI.exe` (voir `docs/contexte/actualiseui_dialogue.md`).

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
   lancé directement par l'utilisateur, ni par aucun raccourci — voir
   point 2 ci-dessous pour le raccourci réel, qui pointe vers
   l'application cible elle-même.

2. **Le setup.exe de chaque application cible** (ex. Scrabble,
   Rummikub) — **ne déploie plus** `Actualise.exe`/`_internal\`/
   `ActualiseUI.exe` lui-même (ancien comportement où chaque setup cible
   embarquait et réinstallait sa propre copie d'Actualise). Son rôle se
   limite désormais à :
   - déposer son propre `config_<nom>.json` dans `C:\Actualise\`
     (jamais `config_actualise.json`, propriété exclusive du setup
     Actualise) ;
   - créer le raccourci Bureau/menu Démarrer pointant vers
     l'exécutable de l'application cible **elle-même** (ex.
     `Scrabble.exe`), comme n'importe quelle application Windows
     classique : c'est l'application cible elle-même qui, dans son
     propre code (voir INTEGRATION.md, §6), lance `Actualise.exe
     --config <nom>` par un `Popen` non bloquant à son propre démarrage
     — uniquement si `C:\Actualise\Actualise.exe` existe — sans jamais
     attendre sa fin ni bloquer sa propre fenêtre. Le setup de
     l'application cible n'a donc rien de particulier à faire pour
     déclencher Actualise : un raccourci Bureau/menu Démarrer tout à
     fait ordinaire suffit ;
   - déployer son propre fichier `.ico` et l'utiliser à la fois pour le
     champ `IconFilename` du raccourci créé (qui pointe désormais
     directement vers l'exécutable de l'application cible, donc affiche
     naturellement son icône) et pour le champ `icone` de
     `config_<nom>.json` — même chemin dans les deux cas, pour cohérence
     documentée (voir `docs/contexte/configuration.md`, « Contenu des
     fichiers de configuration »).

   Ce découplage préserve la réutilisabilité d'Actualise pour de
   futures applications cibles et sépare le cycle de vie des
   installations : désinstaller une application cible ne désinstalle
   pas nécessairement Actualise, qui continue de gérer les autres
   programmes présents sur la machine (voir point 1 ci-dessus).
