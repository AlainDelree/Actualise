# État du système — Actualise et ses clients

## Versions publiées
- Actualise v11 — publié sur GitHub (Release v11) ; la Release contient
  DEUX assets, `Actualise-Setup-v11.exe` et `actualise-v11.zip` —
  décision d'Alain : à l'avenir, comme pour Scrabble et Rummikub, la
  Release contiendra toujours l'installeur ET l'archive
- Scrabble v13 — publié sur GitHub (Release v13)
- Rummikub v13 — publié sur GitHub (Release v13)

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
3. Installer Actualise-Setup-v11.exe (pris dans la Release v11)
4. Installer Scrabble-Setup-v13.exe
5. Installer Rummikub-Setup-v13.exe
6. Lancer verifier_installation.py pour confirmer
7. Lancer Scrabble

## Processus de build et de publication
- `build\rebuild_actualise_unifie.bat --publier [--build N]` (issue #67)
  construit l'exécutable, l'installeur et l'archive, écrit
  `version.json` et fait un commit local ; il ne pousse jamais et ne
  crée jamais de Release — il recopie l'installeur et l'archive vers
  `C:\CCW_Share\_derniers_builds\actualise\` avec le numéro de build réel
- Ordre de publication manuel recommandé (guide BUILD_WINDOWS_CCW.md de
  Bridge_Agent) : fusionner la branche du build sans pousser, créer la
  Release (étiquette v<N>, deux fichiers attachés), puis pousser master

## Points en suspens
- Builds CCW sur le PC fixe Windows (partage Samba) validés le 20 août 2026 :
  chaîne PyInstaller + ISCC fonctionnelle, Actualise-Setup-v9.exe produit
  sans erreur.
- verifier_installation.py existe comme script standalone (pas dans un dépôt)
- Cause exacte de l'échec d'extraction observé en Program Files (droits
  insuffisants, ou fichiers verrouillés parce que l'application cible —
  qui lance Actualise à son démarrage — tourne encore) non tranchée ;
  issue #66 traite la façon d'échouer (non fatal, zip conservé) mais pas
  la cause elle-même — à trancher par un test en conditions réelles.
- `build\rebuild_actualise_unifie.bat` a un nom provisoire : à renommer
  `rebuild_actualise.bat` dans une issue ultérieure, après quoi les trois
  anciens scripts (rebuild_actualise.bat, rebuild_actualise_setup.bat,
  publier_actualise.bat) seront retirés, ainsi que les commentaires qui
  les citent (.gitignore, installeur\actualise.iss, actualise.spec).
- Fiabilisation de updater.bat à prévoir (issue pas encore créée) :
  constaté qu'ActualiseUI.exe n'est pas remplacé par la bascule (garde
  la date du build précédent) ; constaté aussi, lors d'un test réel
  v10→v11, qu'une première passe faite avec le code de la v10 peut
  laisser build_installe périmé, corrigé seulement par la passe
  suivante — les PC encore en v10 verront une proposition de mise à
  jour de trop, une seule fois.
- CHANGELOG-67.md reste un fichier séparé à la racine : l'outil de
  relecture ne sait pas l'intégrer à CHANGELOG.md pour un projet du PC
  fixe — intégration à faire.
- Test réel de la mise à jour d'une application cible (Scrabble ou
  Rummikub) par updater.bat, à faire au prochain build d'un jeu.
