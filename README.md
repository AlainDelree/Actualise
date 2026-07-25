# Actualise

Système de mise à jour automatique générique pour applications Windows
packagées en `.exe` (ex. PyInstaller), pensé initialement pour Scrabble
mais réutilisable pour d'autres projets.

## Principe général

Actualise est un exécutable séparé de l'application cible : le
raccourci Bureau/menu Démarrer de l'utilisateur final pointe vers
Actualise, jamais directement vers l'application cible. Au lancement,
Actualise démarre immédiatement l'application cible dans sa version
installée (aucun délai perceptible), puis vérifie et télécharge les
mises à jour disponibles en arrière-plan ; toute mise à jour trouvée
est appliquée au lancement suivant.

Voir [CONCEPTION.md](CONCEPTION.md) pour le rapport de conception
complet (architecture détaillée, format de version, distribution des
binaires, manifeste de mise à jour, séquence de démarrage, garde-fou
anti-boucle infinie, et l'ensemble des décisions actées).

## Structure du projet

- `actualise.py` — point d'entrée principal
- `config.py` — lecture/écriture de `config.json`, chemins portables
- `version_check.py` — vérification de `version.json` (Actualise et
  application cible)
- `mise_a_jour.py` — téléchargement, vérification SHA-256, extraction
  du zip, application du manifeste
- `notifications.py` — envoi de notifications ntfy

## État actuel

Squelette initial : structure de fichiers et signatures de fonctions en
place, implémentation à venir dans des issues suivantes.
