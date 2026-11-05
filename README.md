# Actualise

Système de mise à jour automatique générique pour applications Windows
packagées en `.exe` (ex. PyInstaller), pensé initialement pour Scrabble
mais réutilisable pour d'autres projets. Application complète et
déployée en production (Scrabble, Rummikub) — voir ETAT.md pour le
détail des versions publiées.

## Principe général

Actualise est un exécutable séparé de l'application cible, mais ce
n'est pas lui que l'utilisateur final lance : le raccourci Bureau/menu
Démarrer pointe vers l'application cible elle-même (ex. `Scrabble.exe`),
jamais directement vers Actualise. C'est l'application cible qui, à son
propre démarrage, lance `Actualise.exe --config <nom>` en arrière-plan
(sans attendre sa fin, sans bloquer sa propre fenêtre) si
`C:\Actualise\Actualise.exe` est présent sur la machine. Actualise
vérifie alors et télécharge en arrière-plan les mises à jour
disponibles (pour lui-même et pour l'application cible) ; toute mise à
jour trouvée est appliquée au lancement suivant, jamais pendant la
session en cours.

Voir [CONCEPTION.md](CONCEPTION.md) pour le rapport de conception
complet (architecture détaillée, format de version, distribution des
binaires, manifeste de mise à jour, séquence de démarrage, garde-fou
anti-boucle infinie, et l'ensemble des décisions actées) et
[INTEGRATION.md](INTEGRATION.md) pour le guide pratique d'intégration
d'une nouvelle application cible.

## Structure du projet

- `actualise.py` — point d'entrée principal
- `actualise_ui.py` — fenêtre de dialogue de mise à jour côté
  utilisateur final (compilé séparément en `ActualiseUI.exe`)
- `config.py` — lecture/écriture de `config_actualise.json` et
  `config_<nom_app>.json`, chemins portables
- `version_check.py` — vérification de `version.json` (Actualise et
  application cible)
- `mise_a_jour.py` — téléchargement, vérification SHA-256, extraction
  du zip, application du manifeste
- `notifications.py` — envoi de notifications ntfy
- `build/rebuild_actualise.bat` — construit l'exécutable, l'installeur
  et l'archive, et publie un nouveau build (`--publier`) ; voir ETAT.md,
  « Processus de build et de publication »
- `installeur/actualise.iss` — installeur InnoSetup d'Actualise
  (`Actualise-Setup.exe`)

## Lancement et build

Actualise n'est jamais lancé directement par l'utilisateur ni par un
raccourci : c'est l'application cible qui le lance à son propre
démarrage (voir « Principe général » ci-dessus et INTEGRATION.md, §6,
pour le code exact à intégrer côté application cible).

Pour reconstruire et publier un nouveau build : `build\rebuild_actualise.bat
--publier [--build N]` (voir ETAT.md pour le détail du processus et
l'ordre de publication manuel recommandé).

## Tests

Suite complète : `pytest`.

Les tests de `TestGabaritUpdaterBat` et `TestGabaritUpdaterBatJeu`
(exécution réelle d'`updater.bat`, actifs uniquement sous Windows) sont
marqués `lent` car ils enchaînent des attentes réelles (subprocess,
`time.sleep`). Pour une exécution rapide qui les exclut :
`pytest -m "not lent"`.

## État actuel

Application complète et déployée : voir ETAT.md pour l'état détaillé
des versions publiées et des points en suspens, et TACHES.md pour les
tâches restantes.
