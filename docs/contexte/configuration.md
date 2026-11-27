# Configuration — fichiers et résolution du dossier

## Contenu des fichiers de configuration — `config_actualise.json` / `config_<nom_app>.json`

Deux fichiers séparés, chargés par `config.charger_config(nom_app)`.

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
  "topic_ntfy": "<topic-ntfy>"
}
```

`topic_ntfy` est **facultatif** (voir plus bas) : un `config_<nom_app>.json`
sans ce champ est valide, par exemple pour une application cible qui n'a
pas de topic ntfy dédié.

`config.charger_config(nom_app)` lit les deux fichiers et les fusionne
en un seul dict `{"actualise": ..., "application_cible": ...,
"zone_attente": ..., "topic_ntfy": ...}`, compatible avec la structure
déjà utilisée par le reste d'Actualise (`zone_attente` extrait de
`config_actualise.json`, `topic_ntfy` copié depuis
`application_cible` par commodité pour l'appelant, ou `None` si absent
de `application_cible`). L'absence de l'un ou l'autre fichier, ou un
JSON malformé, reste **bloquant** : `FileNotFoundError`/
`json.JSONDecodeError` remontent telles quelles, sans repli silencieux
— seul `topic_ntfy` fait exception à cette règle de blocage.

Détail des champs :

- `build_installe` (dans `config_actualise.json` **et** dans
  `config_<nom_app>.json`, séparément) : le numéro de build
  actuellement installé pour ce programme, directement comparable au
  champ `build` du `version.json` correspondant (voir
  `docs/contexte/versioning.md`, « Format de version »).
- `depot_github` (dans `config_actualise.json` **et** dans
  `config_<nom_app>.json`) : sert à construire l'URL du `version.json`
  correspondant (voir `docs/contexte/versioning.md`, « Deux fichiers
  `version.json` distincts »).
- `executable` (dans `config_<nom_app>.json`) : nom/chemin du fichier
  exécutable de l'application cible, une fois la bascule éventuelle
  effectuée (étape 3 de la séquence de démarrage, voir
  `docs/contexte/demarrage_reseau.md`).
- `repertoire_installation` (dans `config_<nom_app>.json`) : dossier
  cible pour l'extraction du zip de mise à jour de l'application
  cible ; c'est aussi dans ce dossier — celui de l'application cible,
  pas celui d'Actualise — qu'est écrit `actualise_update.flag` (voir
  `docs/contexte/actualiseui_dialogue.md`).
- `icone` (dans `config_<nom_app>.json`, **optionnel**) : chemin vers
  le fichier `.ico` de l'application cible, déployé par le setup de
  cette application à un emplacement connu (ex. à côté de son
  exécutable). Ce champ est **informationnel/documenté pour Actualise**
  — Actualise n'a pas d'interface graphique et ne le lit **pas** au
  runtime — mais sert de **convention** pour le setup de l'application
  cible : le même chemin `.ico` doit être utilisé à la fois pour ce
  champ et pour le champ `IconFilename` du raccourci créé par ce setup
  (voir `docs/contexte/integration_setup.md`), afin que la
  documentation de `config_<nom_app>.json` reste cohérente avec l'icône
  réellement affichée par le raccourci.
- `zone_attente` (dans `config_actualise.json` uniquement) : chemin du
  dossier où sont stockés les zip téléchargés en arrière-plan avant
  bascule au lancement suivant — **commun** à Actualise et à toutes les
  applications cibles gérées par cette installation, cohérent avec le
  fait qu'il n'existe plus qu'une seule installation d'Actualise à
  gérer (voir « Configuration portable »).
- `topic_ntfy` (dans `config_<nom_app>.json`, **facultatif**) : topic
  ntfy dédié à ce programme, s'il en a un — règle par défaut quand il
  est présent : un topic ntfy dédié par programme géré. Absent, vide
  ou autre chose qu'un texte : Actualise désactive simplement la
  notification ntfy pour cette application cible (aucune erreur,
  aucune interruption du flux de vérification/mise à jour) — c'est le
  cas de **Rummikub**, qui a retiré ntfy (son issue #271) et dont
  l'installeur n'écrit plus ce champ. **Cas particulier Scrabble** :
  pour ce projet spécifiquement, `topic_ntfy` réutilise le topic déjà
  existant des notifications d'issues fermées de Bridge_Agent pour
  Scrabble — pas de topic dédié séparé créé, car seul Alain est abonné
  aux deux flux et le préfixe `"MAJ - "` des notifications d'Actualise
  suffit à les distinguer visuellement des notifications de clôture
  d'issue dans le même flux. Le principe général « un topic ntfy dédié
  par programme géré » reste la règle par défaut pour de futurs projets
  ayant un public destinataire différent (ex. un autre utilisateur
  final abonné) ; Scrabble est un cas particulier documenté comme tel,
  pas un changement de règle générale.

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
mode PyInstaller figé (`sys.frozen`). `Actualise.exe` n'étant installé
qu'une seule fois, à un emplacement fixe (`C:\Actualise\`, imposé par le
setup dédié — voir `docs/contexte/integration_setup.md`), cette
résolution relative pointe systématiquement vers ce même dossier
partagé, quelle que soit l'application cible qui a lancé Actualise. En
mode script non figé (développement/tests), repli sur
`%SYSTEMDRIVE%\Actualise\`.

Sous Linux, le comportement reste inchangé (`~/.config/actualise/` ou
variable d'environnement `ACTUALISE_CONFIG_DIR`) : l'exécutable Linux
n'étant pas installé par un setup Windows par application, la
problématique de collision multi-installations ne s'y pose pas de la
même façon.
