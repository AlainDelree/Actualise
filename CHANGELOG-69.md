## Issue #69 — Mise à jour ETAT.md et TACHES.md après la publication d'Actualise v11

- ETAT.md : « Versions publiées » passe de v10 à v11, précise que la
  Release v11 contient DEUX assets (installeur + archive), retire la
  phrase sur le non-republiement de l'installeur et la mention
  d'Actualise-Setup-v9.exe.
- ETAT.md : procédure de déploiement mise à jour pour utiliser
  Actualise-Setup-v11.exe (Release v11).
- ETAT.md : nouvelle section « Processus de build et de publication »
  (build\rebuild_actualise_unifie.bat --publier, ordre de publication
  manuel recommandé).
- ETAT.md : « Points en suspens » complété (renommage du script de
  build, fiabilisation de updater.bat dont ActualiseUI.exe, intégration
  de CHANGELOG-67.md, test réel de mise à jour d'un jeu à venir) ; le
  point sur la cause de l'échec d'extraction est conservé tel quel.
- TACHES.md : l'entrée sur les noms d'assets versionnés (réalisée) est
  retirée et remplacée par les quatre tâches restantes listées ci-dessus.

Aucun code ni test touché — documentation uniquement.
