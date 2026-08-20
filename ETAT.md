# État du système — Actualise et ses clients

## Versions publiées
- Actualise v9 — publié sur GitHub, installé et fonctionnel
- Scrabble v12 — publié sur GitHub (Release v12), build officiel avec commits leave_value (moteur IA amélioré) et nouveau setup sans Actualise
- Rummikub v12 — publié sur GitHub (Release v12), nouveau setup sans Actualise
- Actualise-Setup-v9.exe — nouvel installeur indépendant créé et buildé

## Architecture en place (refonte complète effectuée)
- Raccourcis → exe direct (Scrabble.exe / Rummikub.exe), plus via Actualise
- Les jeux lancent Actualise au démarrage si présent (C:\Actualise\Actualise.exe), tournent sans lui si absent
- Les setups jeux n'embarquent plus Actualise — ils déposent uniquement leur config_<jeu>.json dans C:\Actualise\
- Actualise ne lance plus aucun jeu
- Actualise-Setup.exe installe Actualise indépendamment

## Procédure de déploiement sur les anciens PC (validée)
1. Désinstaller Actualise (Paramètres Windows)
2. Supprimer C:\Actualise\ manuellement
3. Installer Actualise-Setup-v9.exe
4. Installer Scrabble-Setup-v12.exe
5. Installer Rummikub-Setup-v12.exe
6. Lancer verifier_installation.py pour confirmer
7. Lancer Scrabble

## Points en suspens
- Builds CCW sur le nouveau PC fixe Windows (Samba, remplace la VM
  VirtualBox) validés le 20 août 2026 : chaîne PyInstaller + ISCC
  fonctionnelle, Actualise-Setup-v9.exe produit sans erreur.
- verifier_installation.py existe comme script standalone (pas dans un dépôt)
