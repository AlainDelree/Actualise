# Distribution des binaires et manifeste de mise à jour

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

**Nom de fichier de l'asset : versionné, `<préfixe>-v<build>.zip`.**
L'asset publié pour chaque Release porte un nom différent à chaque
build : **`<préfixe>-v<build>.zip`** (ex. `actualise-v48.zip`,
`scrabble-v48.zip`), construit par `_url_asset_release` à partir du
préfixe et du numéro de build. Le tag de la Release suit le même
numéro, au format **`v<build>`** (ex. `v48`), directement dérivé de
l'entier incrémental déjà acté (voir `docs/contexte/versioning.md`,
« Format de version ») — le nom de fichier de l'asset et le tag
portent donc la même information de version, de façon redondante mais
cohérente. Ce choix aligne Actualise sur le nommage déjà utilisé pour
les applications cibles (ex. `Scrabble-Setup-v10.exe`) plutôt que
d'introduire une convention différente ; il évite aussi de dépendre
d'une URL « latest » qui resterait implicite, la publication d'une
nouvelle Release restant de toute façon pilotée manuellement par Alain,
au moment de son choix — pas à chaque commit. Conséquence pratique :
chaque nouvelle Release uploade un nouvel asset au nom incluant son
propre numéro de build — les anciens assets de builds précédents
restent disponibles sur GitHub sans être écrasés, mais seul le build
indiqué par `version.json` est téléchargé par Actualise.

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
  acté (voir `docs/contexte/versioning.md`, « Format de version »).
- `supprimer` : liste **optionnelle** de chemins relatifs (au dossier
  d'installation) à supprimer après extraction du zip. C'est une **liste
  noire explicite** : seuls les chemins listés sont supprimés, rien
  d'autre n'est touché — **fail-safe** par construction, puisqu'un oubli
  dans cette liste laisse au pire un fichier obsolète inoffensif sur le
  disque, jamais une perte de données par suppression involontaire
  (contrairement à une logique de liste blanche, où un oubli pourrait
  effacer un fichier qui aurait dû être conservé).

**Choix écarté : script exécutable (`.bat`/`.sh`) en post-traitement**,
au profit d'un manifeste JSON déclaratif, pour deux raisons :
portabilité Linux/Windows (un `.bat` n'a pas d'équivalent direct côté
Linux) et sécurité (exécuter un script téléchargé sans supervision ouvre
une surface de risque bien plus large qu'une suppression bornée à une
liste de chemins explicites).

**Cas limite : `manifest.json` absent de l'archive.** Traité comme
**bloquant** : la bascule de cette mise à jour échoue et n'est pas
appliquée (ni extraction, ni suppression, ni lancement de la version
mise à jour). Le zip **n'est pas supprimé** de `zone_attente` : une
nouvelle tentative a lieu au prochain cycle de vérification en
arrière-plan (le zip reste re-téléchargé puis réappliqué à ce cycle).
Raison de ce choix : un zip sans manifeste est considéré **malformé**
plutôt que de supposer silencieusement « rien à supprimer » — un
manifeste manquant est plus probablement le signe d'un problème de
publication (asset incomplet, erreur de packaging) qu'une intention
volontaire de l'auteur de la Release.
