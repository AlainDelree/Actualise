# État du système — Actualise et ses clients

## Versions publiées
- Actualise v10 — publié sur GitHub (Release v10) ; la Release ne
  contient que l'asset `actualise-v10.zip` (zip de mise à jour), pas
  l'installeur — `Actualise-Setup.exe` n'est pas republié à chaque build
  d'Actualise
- Scrabble v13 — publié sur GitHub (Release v13)
- Rummikub v13 — publié sur GitHub (Release v13)
- Actualise-Setup-v9.exe — dernier installeur indépendant buildé (voir
  ci-dessous : Actualise lui-même se met à jour en v10 par son propre
  mécanisme, sans nouvel installeur)

## Architecture en place (refonte complète effectuée)
- Raccourcis → exe direct (Scrabble.exe / Rummikub.exe), plus via Actualise
- Les jeux lancent Actualise au démarrage si présent (C:\Actualise\Actualise.exe), tournent sans lui si absent
- Les setups jeux n'embarquent plus Actualise — ils déposent uniquement leur config_<jeu>.json dans C:\Actualise\
- Actualise ne lance plus aucun jeu
- Actualise-Setup.exe installe Actualise indépendamment
- Les anciennes versions de Rummikub (v7 et antérieures, raccourci
  pointant encore vers Actualise.exe au lieu de Rummikub.exe) ne
  peuvent pas se mettre à jour seules vers cette nouvelle architecture :
  elles exigent une installation manuelle du setup courant (pas de
  bascule automatique du raccourci)

## Procédure de déploiement sur les anciens PC (validée)
1. Désinstaller Actualise (Paramètres Windows)
2. Supprimer C:\Actualise\ manuellement — **indispensable** :
   Actualise-Setup.exe ne réécrit volontairement pas un
   config_actualise.json déjà présent (pour ne pas écraser build_installe
   d'une installation existante), donc un ancien config_actualise.json
   laissé en place après désinstallation ferait repartir la nouvelle
   installation avec un build périmé
3. Installer Actualise-Setup-v9.exe
4. Installer Scrabble-Setup-v13.exe
5. Installer Rummikub-Setup-v13.exe
6. Lancer verifier_installation.py pour confirmer
7. Lancer Scrabble

## Points en suspens
- Builds CCW sur le nouveau PC fixe Windows (Samba, remplace la VM
  VirtualBox) validés le 20 août 2026 : chaîne PyInstaller + ISCC
  fonctionnelle, Actualise-Setup-v9.exe produit sans erreur.
- verifier_installation.py existe comme script standalone (pas dans un dépôt)
- Cause exacte de l'échec d'extraction observé en Program Files (droits
  insuffisants, ou fichiers verrouillés parce que l'application cible —
  qui lance Actualise à son démarrage — tourne encore) non tranchée ;
  issue #66 traite la façon d'échouer (non fatal, zip conservé) mais pas
  la cause elle-même — à trancher par un test en conditions réelles.
