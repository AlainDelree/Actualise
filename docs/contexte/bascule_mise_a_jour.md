# Bascule et garde-fou anti-boucle

## Garde-fou anti-boucle infinie

Le garde-fou par marqueur reste nécessaire pour l'auto-mise-à-jour
d'Actualise, mais s'inscrit dans le flux non bloquant décrit dans
`docs/contexte/demarrage_reseau.md` : le relancement parent → enfant
n'intervient que pour **appliquer une mise à jour déjà téléchargée**
(bascule locale rapide), jamais pour attendre une vérification réseau en
tout début d'exécution.

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

**Bascule sécurisée par dossier temporaire + renommage.** Une extraction
directe du zip d'Actualise dans son propre dossier d'installation
(`repertoire_installation`, celui de l'exécutable en cours
d'exécution) échoue sous Windows avec `PermissionError [Errno 13]` :
un `.exe` en cours d'exécution ne peut pas être réécrit en place,
seulement renommé.

Ce risque concerne aussi bien Actualise que l'application cible :
celle-ci lance `Actualise.exe --config <nom>` par un `Popen` non
bloquant à son propre démarrage puis continue de tourner sans
l'attendre (voir `docs/contexte/vue_ensemble.md`, « Principe de
fonctionnement ») — son exécutable est donc, dans le cas normal,
**toujours** en cours d'exécution pendant qu'Actualise tente d'appliquer
sa mise à jour. Un zip d'application cible ne s'applique donc jamais par
extraction directe au démarrage, seulement via le mécanisme flag + bat
décrit dans `docs/contexte/actualiseui_dialogue.md` et
`docs/contexte/maj_application_cible.md`.

Pour Actualise lui-même, la bascule suit ce mécanisme :

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

## Vérification SHA-256 à l'application (sidecar, SEC-022)

En plus du contrôle SHA-256 fait au téléchargement (voir
`docs/contexte/demarrage_reseau.md`), l'empreinte est conservée dans un
fichier sidecar `<zip>.sha256` à côté du zip en zone d'attente, re-lue
et recomparée juste avant application au lancement suivant. Un zip
altéré sur le disque entre le téléchargement et ce lancement, ou sans
sidecar (zip mis en attente par une version antérieure à ce correctif),
n'est jamais appliqué — fail-safe. Dans les deux cas, le zip (et son
sidecar) est retiré de la zone d'attente plutôt que rejoué à chaque
lancement, pour être retéléchargé avec son empreinte au prochain
contrôle.

## Limite connue : zip non re-contrôlé entre génération et lancement du bat (audit issue #92)

L'empreinte SHA-256 est contrôlée au téléchargement, puis re-contrôlée à
chaque exécution d'Actualise pour les mises à jour de jeux, et pour
Actualise lui-même seulement quand aucun flag n'existe déjà (sinon la
boucle saute ce zip, en attente de validation utilisateur ou bat déjà
lancé — voir `appliquer_mises_a_jour_en_attente`) ; dans les deux cas,
rien ne re-contrôle le zip entre la génération du bat et son lancement.
Deux chemins de lancement concernés : ActualiseUI au clic sur « Mettre
à jour » (supprime le flag puis lance le bat), et le lancement direct du
bat par l'application cible à sa fermeture quand le flag existe encore
(ex. après « Plus tard ») — ce second chemin est dans le code des
applications cibles, hors de ce dépôt. Ce que le contrôle protège
réellement : une altération accidentelle ou partielle du zip sur le
disque ; l'empreinte conservée à côté du zip ne protège ni contre une
personne pouvant écrire dans la zone d'attente, ni contre une
compromission de la source (SEC-023, risque accepté et consigné dans
`.audit.json`). Pistes écartées pour l'instant : contrôle dans
ActualiseUI au clic (ne couvrirait pas le lancement direct à la
fermeture) ; contrôle dans le gabarit du bat (non retenu).

## Garde anti-évasion de chemin (« zip-slip ») à l'application (audit issues #92/#117, SEC-025)

Une évasion de chemin détectée pendant l'extraction Python de
l'auto-mise-à-jour d'Actualise (`mise_a_jour.extraire_zip`, utilisée par
`appliquer_mises_a_jour_en_attente` quand aucun flag n'est encore en
attente) est un saut propre (log + zip rejeté), plus une exception non
rattrapée qui remontait jusqu'à planter le programme. Les deux autres
chemins d'extraction — tous deux par PowerShell `Expand-Archive` dans un
`updater*.bat` généré, qui n'a pas cette garde — sont protégés sans la
dupliquer en PowerShell : les entrées du zip sont validées côté Python
avec la même garde (`mise_a_jour.valider_entrees_zip`, factorisée depuis
`extraire_zip`) avant même de générer/lancer le bat correspondant,
contre le dossier où `Expand-Archive` extrait réellement (`EXTRACT_DIR`
du gabarit, le sous-dossier `maj_bat` sous le dossier sur lequel le bat
fait `cd /d` en tout début de script — jamais le dossier d'installation
lui-même) :

- mise à jour d'un jeu, détectée au téléchargement ou relancée au
  lancement suivant (`_assurer_maj_jeu_en_attente`) ;
- mise à jour d'Actualise lui-même, détectée par la tâche de vérification
  en arrière-plan (`tache_verification_arriere_plan`) — ce chemin n'avait
  initialement aucune garde (SEC-025, audit issue #117, corrigé par
  l'issue #103), contrairement aux deux autres déjà protégés.

Dans les trois cas, un zip rejeté est retiré de la zone d'attente (pas
rejoué à chaque lancement) ; un zip illisible (`BadZipFile`) est traité
comme transitoire (zip conservé pour une nouvelle tentative), jamais
comme une évasion.

## Noms d'entrées de premier niveau d'un zip de jeu (audit issue #117, SEC-024)

Le bat de mise à jour d'un jeu reçoit les noms d'entrées de premier
niveau de l'archive (`_lister_entrees_racine_zip`) et les écrit
directement dans des commandes batch (`_bloc_bascule_entree_jeu` et les
blocs d'annulation/nettoyage associés), sans échappement. Avant de
générer ce bat, `_assurer_maj_jeu_en_attente` valide donc chaque nom
d'entrée avec `_entree_racine_jeu_valide` : liste blanche prudente (dans
l'esprit de `_nom_jeu_valide`, qui valide déjà le nom de l'application
elle-même) qui accepte les noms réels de premier niveau d'un zip de jeu
— lettres (y compris accentuées), chiffres, espaces et points internes
(ex. `Scrabble.exe`, `_internal`, `data`) — mais refuse un nom vide, `.`
ou `..` (ou en contenant), un nom commençant/finissant par un espace ou
un point, tout caractère de contrôle, tout séparateur de chemin, tout
chemin absolu/lecteur, et les caractères spéciaux de cmd.exe (`%`, `!`,
`^`, `&`, `|`, `<`, `>`, `"`) qui permettraient une injection de
commande dans le bat généré. Un nom rejeté est traité comme une évasion
de chemin : zip et empreinte retirés, ni bat ni flag écrits.

## Bootstrap séparé (écarté)

Actualise reste un exécutable unique qui se met à jour lui-même, avec le
garde-fou par marqueur ci-dessus.
