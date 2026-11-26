# Démarrage et vérification réseau

## Vérification réseau — timeout strict

Toute requête HTTP de vérification de version (`version.json`, Actualise
ou application cible) doit utiliser un **timeout court (2 à 3
secondes)**. Passé ce délai, la vérification est traitée comme un échec
réseau : repli silencieux sur la version installée, sans bloquer
l'utilisateur.

## Séquence de démarrage — vérification non bloquante

Principe central : **Actualise ne bloque jamais, et ne lance plus
aucune application cible.** C'est l'application cible qui lance
Actualise à son propre démarrage (et non l'inverse) ; Actualise se
limite à l'auto-mise-à-jour et à la vérification/téléchargement en
arrière-plan, puis se termine.

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
     prochain lancement) — sauf pour une mise à jour de jeu dont le zip,
     pourtant validé au téléchargement, est ensuite rejeté par
     `_assurer_maj_jeu_en_attente` (nom d'application ou d'entrée de zip
     invalide, évasion de chemin, voir
     `docs/contexte/bascule_mise_a_jour.md`, « Noms d'entrées de premier
     niveau d'un zip de jeu ») : cette notification serait alors fausse,
     puisque le zip vient d'être retiré (issue #105, point 3).

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
   chose, Actualise applique les mises à jour mises en attente
   (`appliquer_mises_a_jour_en_attente`). Le détail diffère
   **fondamentalement** selon qu'il s'agit d'Actualise lui-même ou de
   l'application cible (voir `docs/contexte/actualiseui_dialogue.md`
   et `docs/contexte/maj_application_cible.md` pour le mécanisme complet
   de mise à jour d'un jeu) :
   - **Actualise lui-même** : si une nouvelle version est en attente **et
     qu'aucun flag `actualise_update.flag` n'est déjà présent**,
     bascule immédiate et silencieuse — **extraction du zip** dans un
     dossier temporaire, **bascule par renommage** vers le dossier
     d'installation, puis **application du manifeste** (suppression des
     fichiers listés dans `supprimer`, voir
     `docs/contexte/distribution_releases.md`, « Manifeste de mise à
     jour ») — suivie d'un relancement d'Actualise comme **2ème
     instance** de lui-même avec le **marqueur explicite** parent →
     enfant décrit dans `docs/contexte/bascule_mise_a_jour.md`, avant de
     terminer le parent ; ces opérations restent locales, donc quasi
     instantanées — elles ne réintroduisent pas d'attente réseau
     perceptible. Si un flag est déjà présent, cette bascule silencieuse
     est sautée : le bat/la fenêtre a la main exclusive (voir
     `docs/contexte/actualiseui_dialogue.md`).
   - **Application cible (un jeu)** : **jamais** d'extraction directe,
     quel que soit l'état du flag — un zip de jeu ne s'applique plus que
     via le bat généré pour lui (voir
     `docs/contexte/maj_application_cible.md`), déclenché par le jeu
     lui-même à sa fermeture. Si aucun flag n'est déjà présent dans son
     dossier d'installation, Actualise se contente ici de (re)générer ce
     bat + le flag correspondant si besoin (retry en cas d'échec
     transitoire de génération à un cycle précédent) ; `build_installe`
     et le zip ne sont modifiés/supprimés que par le bat, jamais ici.

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
