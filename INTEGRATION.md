# Intégration — guide pratique pour une application cible

## 1. Objectif

Guide pratique destiné à une conversation Claude qui intègre une nouvelle application cible avec Actualise. Complète CONCEPTION.md qui reste la référence architecturale.

## 2. Architecture générale

Actualise est une instance unique partagée entre toutes les applications cibles, installée dans `C:\Actualise\`. Chaque application cible a son propre fichier de configuration dans ce dossier. Actualise est lancé avec `--config <nom>` pour savoir quelle application gérer.

## 3. Checklist d'intégration pour un nouveau projet cible

- **Droits d'installation** : le setup doit utiliser `PrivilegesRequired=admin` (jamais `lowest`) pour pouvoir créer et écrire dans `C:\Actualise\` (racine du disque système, inaccessible en écriture aux utilisateurs standards). Avec `admin`, les constantes InnoSetup `{autopf}`, `{autodesktop}` et `{autoprograms}` résolvent vers les emplacements "tous les utilisateurs" (C:\Program Files\, Bureau commun, menu Démarrer commun). Incident réel : avec `lowest`, Actualise n'est pas déployé, le raccourci pointe vers l'ancienne installation et l'application ne démarre pas.
- **Dossier Actualise partagé** : `C:\Actualise\` — jamais un dossier par app.
- **Deux fichiers de config** à créer par le setup InnoSetup :
  - `C:\Actualise\config_actualise.json` — uniquement s'il n'existe pas déjà (ne pas écraser si une autre app l'a déjà créé).
  - `C:\Actualise\config_<nom>.json` — spécifique à cette app (ex. `config_scrabble.json`).
- **Trois exécutables** à déployer dans `C:\Actualise\` par le setup :
  - `Actualise.exe`
  - `_internal\` (dossier complet — jamais l'exe seul, incident réel : `Failed to load Python DLL` si `_internal\` manque)
  - `ActualiseUI.exe` (exécutable séparé, inclus dans `actualise-v<N>.zip`)
  - Déployer uniquement si la version embarquée est plus récente que celle déjà présente (InnoSetup gère ça nativement).
- **Raccourci** Bureau pointant vers `C:\Actualise\Actualise.exe` avec l'argument `--config <nom>` (ex. `--config scrabble`). Ne jamais pointer vers l'exécutable de l'app cible directement.
- **Icône du raccourci** : fichier `.ico` propre à l'app cible, même chemin dans `config_<nom>.json` (champ `icone`).
- **Nettoyage de l'ancien dossier** : si `C:\Actualise_<NomApp>\` existe (ancienne architecture), le supprimer entièrement lors de l'installation.
- **Désinstallation** : supprimer `config_<nom>.json` mais pas `C:\Actualise\` si d'autres `config_*.json` y existent encore.
- **Intégration dans le code de l'app cible** : voir §6.

## 4. Format des fichiers de configuration

### config_actualise.json (partagé, ne pas écraser s'il existe)
```json
{
  "build_installe": 8,
  "depot_github": "AlainDelree/Actualise",
  "zone_attente": "C:\\Actualise\\attente\\"
}
```
`build_installe` doit refléter la version réelle d'Actualise embarquée, lue dynamiquement depuis le zip téléchargé — jamais une valeur figée en dur (incident réel : boucle de fausse détection si la valeur ne correspond pas).

### config_<nom>.json (spécifique à l'app)
```json
{
  "nom": "Scrabble",
  "depot_github": "AlainDelree/Scrabble",
  "build_installe": 8,
  "repertoire_installation": "C:\\Scrabble\\",
  "executable": "Scrabble.exe",
  "icone": "C:\\Scrabble\\Scrabble.ico",
  "topic_ntfy": "mon-topic-ntfy"
}
```

## 5. Format des Releases GitHub de l'application cible

- Asset zip nommé `<prefixe>-v<build>.zip` (ex. `scrabble-v8.zip`) — Actualise construit l'URL dynamiquement à partir du numéro de build.
- Tag GitHub : `v<build>` (ex. `v8`).
- Le zip doit être à plat : exécutable et `_internal\` directement à la racine, sans sous-dossier intermédiaire.
- Inclure un `manifest.json` à la racine : `{"supprimer": []}`.
- L'app cible doit publier son propre `version.json` à la racine du dépôt : `{"build": N, "sha256": "..."}`.

## 6. Intégration dans le code de l'application cible

Deux ajouts dans le code de l'app, une seule fois, jamais à modifier ensuite.

### Au démarrage (avant l'ouverture de la fenêtre)
```python
import json
import subprocess
from pathlib import Path

_flag = Path(sys.executable).parent / "actualise_update.flag"
if _flag.exists():
    try:
        _data = json.loads(_flag.read_text(encoding="utf-8"))
        subprocess.Popen([
            _data["actualise_ui"],
            "--bat", _data["bat"],
            "--flag", str(_flag),
            "--relancer", sys.executable,
        ])
    except Exception:
        pass  # ne jamais bloquer le démarrage
```

### À la fermeture de la fenêtre principale
Adapter à la technologie UI utilisée (pywebview `window.events.closing`, tkinter `WM_DELETE_WINDOW`, etc.) :
```python
def _handler_fermeture_actualise():
    _flag = Path(sys.executable).parent / "actualise_update.flag"
    if _flag.exists():
        try:
            _data = json.loads(_flag.read_text(encoding="utf-8"))
            _flag.unlink(missing_ok=True)
            subprocess.Popen([_data["bat"]], shell=True)
        except Exception:
            pass
```

## 7. Workflow de publication (build script)

- Numéro de build auto-incrémenté (ou forçable explicitement).
- SHA-256 du zip calculé automatiquement.
- `version.json` mis à jour et commit local automatisé.
- `git push` et création de la Release GitHub toujours manuels.
- URL de téléchargement d'Actualise dans le script de build : toujours pointer vers la dernière Release Actualise disponible — ne jamais hardcoder un numéro de version.

## 8. Convention ntfy

`topic_ntfy` peut être réutilisé depuis un topic existant (avec préfixe `"MAJ - "` pour distinguer les messages) ou dédié à l'application cible. Les deux sont valables.

## 9. Bug bootstrap connu

Les installations encore sur Actualise ≤ v2 ne peuvent pas s'auto-mettre-à-jour — le mécanisme de bascule contenait un bug qui empêche la mise à jour vers v3+. Ces machines doivent être réinstallées manuellement avec un setup embarquant une version récente d'Actualise.
