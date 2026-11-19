# Versioning — `version.json` et zips versionnés

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
applicatif (voir « Séquence de démarrage » dans
`docs/contexte/demarrage_reseau.md` pour son usage).

**Piège explicite à éviter** : comparer `version.json` comme des
chaînes de caractères donne un résultat lexicographiquement incorrect
(ex. la chaîne `"9"` est jugée supérieure à `"10"`). L'entier
incrémental élimine ce piège par construction et reste trivial à
générer à chaque publication (incrémentation simple).

## Deux fichiers `version.json` distincts

- Un `version.json` dans le **dépôt Actualise** — version d'Actualise
  lui-même.
- Un `version.json` dans le **dépôt de chaque application cible** (ex.
  Scrabble) — l'URL de ce fichier est construite à partir des
  informations du fichier `config_<nom_app>.json` local (dépôt GitHub
  cible).

Les deux logiques de mise à jour (Actualise vs application cible) sont
**indépendantes** : chacune a son propre `build` courant, sa propre
vérification réseau, son propre téléchargement.

## Nommage versionné des zips en zone d'attente

Convention de nommage dans `zone_attente` : `<préfixe>_<build>.zip` (ex.
`actualise_48.zip`, `scrabble_112.zip`). Le préfixe identifie à qui
appartient le zip (`actualise`, ou le nom de l'application cible tel
que défini dans `config_<nom_app>.json`) ; le numéro de build permet la
comparaison directe avec le `build_installe` correspondant (voir
`docs/contexte/configuration.md`, « Contenu des fichiers de
configuration ») sans avoir à ouvrir le zip ni consulter un fichier
séparé.

Comportement au démarrage, **avant bascule** (étape 3 de la séquence de
démarrage, voir `docs/contexte/demarrage_reseau.md`) : pour chaque
préfixe connu (`actualise`, nom de l'application cible), si un fichier
`<préfixe>_<build>.zip` existe dans `zone_attente` :

- si `build` > `build_installe` correspondant → mise à jour valide,
  bascule appliquée (extraction + manifeste, voir l'étape 3 de la
  séquence de démarrage), puis le zip est **supprimé après succès** de
  la bascule ;
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
garde-fou par marqueur décrit dans `docs/contexte/bascule_mise_a_jour.md`
(« Garde-fou anti-boucle infinie »).

## Cache CDN de `version.json`

Servi via `raw.githubusercontent.com`, le fichier `version.json` est mis
en cache par le CDN GitHub (~5 minutes). La détection d'une nouvelle
version peut donc être retardée d'autant après une publication. Jugé
acceptable pour l'usage visé (pas de mise à jour urgente à la minute
près), mais documenté ici pour mémoire — une éventuelle parade
(paramètre anti-cache, endpoint API GitHub, ou tag Release) reste
ouverte si le délai devenait gênant.
