# ActualiseUI.exe — dialogue de mise à jour côté utilisateur final

Mécanisme complémentaire à la bascule silencieuse décrite dans
`docs/contexte/bascule_mise_a_jour.md` (« Garde-fou anti-boucle
infinie »), pour le même problème de fond (le verrou Windows sur
`_internal\`/`Actualise.exe` pendant qu'Actualise tourne), mais en
donnant cette fois la main à l'utilisateur final plutôt qu'en
l'appliquant silencieusement. C'est un **exécutable séparé**,
`ActualiseUI.exe` (`actualise_ui.py`, compilé en `--onefile` via
`actualise_ui.spec`), jamais importé par `actualise.py` : une petite
fenêtre tkinter (« Mettre à jour » / « Plus tard »), sans dépendance
externe, dont le seul rôle est de présenter le choix à l'utilisateur
final et de déclencher un `.bat` généré par Actualise.

Déroulé :

1. Dès que la tâche de fond (« Séquence de démarrage », étape 2 — voir
   `docs/contexte/demarrage_reseau.md`) détecte et télécharge une
   nouvelle version d'**Actualise lui-même**, elle génère immédiatement,
   en plus du zip placé en zone d'attente :
   - `updater.bat`, dans le dossier partagé d'Actualise
     (`C:\Actualise\`) — script qui effectue la bascule réelle des
     **trois** éléments (`_internal\`, `Actualise.exe` et
     `ActualiseUI.exe`, chacun renommé en `.old` puis remplacé par
     renommage/déplacement, jamais un déplacement direct vers un nom
     encore existant), avec attente réelle de la fin de
     `Actualise.exe`/`ActualiseUI.exe` (sinon abandon sans rien
     modifier), contrôle de chaque étape avec restauration de l'état
     initial en cas d'échec, `build_installe` réécrit et zip/flag
     supprimés seulement après bascule confirmée, et journal
     `updater.log` (borné en taille) dans `dossier_actualise` ;
   - `actualise_update.flag`, un JSON déposé dans le
     `repertoire_installation` de **l'application cible** (pas dans le
     dossier d'Actualise), contenant les chemins vers `ActualiseUI.exe`
     et vers `updater.bat`.
2. L'application cible (voir INTEGRATION.md, §6, pour le code exact à
   intégrer une fois pour toutes) détecte ce flag à son propre
   démarrage et lance `ActualiseUI.exe --bat ... --flag ... --relancer
   <son propre exécutable>`, qui affiche la fenêtre de choix.
   - **« Mettre à jour »** : supprime le flag, lance `updater.bat` (qui
     relance l'application cible une fois la bascule terminée, via
     `--relancer`), ferme la fenêtre.
   - **« Plus tard »** : ferme simplement la fenêtre, flag conservé —
     le choix sera reproposé au prochain démarrage.
3. À la **fermeture** de la fenêtre principale de l'application cible,
   si le flag existe encore (mise à jour jamais validée via la
   fenêtre), l'application cible lance directement `updater.bat` (sans
   fenêtre, sans demander confirmation) avant de se fermer. Ceci
   garantit que la mise à jour d'Actualise finit **toujours** par
   s'appliquer — au plus tard à la prochaine fermeture normale de
   l'application cible — même si l'utilisateur ignore systématiquement
   la fenêtre de choix.
4. Tant que ce flag existe, `appliquer_mises_a_jour_en_attente` (étape
   3 de la « Séquence de démarrage ») **saute** la bascule silencieuse
   par renommage pour Actualise : `ActualiseUI.exe`/`updater.bat` a
   alors la main exclusive, pour éviter une double bascule concurrente.
   La bascule silencieuse par renommage (voir
   `docs/contexte/bascule_mise_a_jour.md`, « Garde-fou anti-boucle
   infinie ») reste le mécanisme de **repli** : si le flag/bat n'a pas
   pu être généré (`OSError`), Actualise applique la mise à jour
   lui-même, sans interface, comme avant l'introduction d'`ActualiseUI.exe`.

Ce mécanisme sert aussi à la mise à jour d'une application cible — voir
`docs/contexte/maj_application_cible.md` pour sa généralisation.
