# Changelog — issue #85

## Issue #85 — Audit #92 : CONCEPTION.md, documenter les moments où l'empreinte du zip est contrôlée et la limite connue

- **Documentation** : ajout d'une ligne dans la table des décisions
  actées de `CONCEPTION.md`, juste après « Vérification SHA-256 du
  zip » et avant « Garde anti-évasion de chemin (« zip slip ») à
  l'application » : « Limite connue : zip non re-contrôlé entre
  génération et lancement du bat (audit issue #92) ». Elle récapitule
  les deux moments où l'empreinte SHA-256 est contrôlée (téléchargement,
  puis re-contrôle à chaque exécution pour les mises à jour de jeux et
  seulement en l'absence de flag pour Actualise lui-même), signale la
  limite connue — aucun contrôle entre la génération du bat et son
  lancement, sur les deux chemins de lancement concernés (clic
  « Mettre à jour » d'ActualiseUI, lancement direct du bat par
  l'application cible à sa fermeture) —, précise ce que le contrôle
  protège réellement (altération accidentelle ou partielle du zip, pas
  une compromission de la source ni un accès en écriture à la zone
  d'attente, risque SEC-023 déjà accepté dans `.audit.json`), et
  mentionne les deux pistes écartées pour l'instant (contrôle au clic
  dans ActualiseUI, contrôle dans le gabarit du bat). Aucun autre
  fichier modifié.
