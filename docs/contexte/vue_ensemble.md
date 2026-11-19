# Vue d'ensemble — Actualise

## Contexte et objectif

Système de mise à jour automatique générique, pensé initialement pour
Scrabble mais conçu pour être réutilisable sur d'autres projets. Permet à
un utilisateur final (ex. la maman d'Alain) de toujours disposer de la
dernière version stable d'une application Windows packagée en .exe
(PyInstaller ou autre), sans réinstallation manuelle à chaque mise à jour.

## Principe de fonctionnement

Un exécutable séparé de l'application cible (contournement du problème
classique : un .exe ne peut pas se remplacer lui-même pendant qu'il
s'exécute). **Comportement réel actuel** (voir « Séquence de démarrage »
dans `docs/contexte/demarrage_reseau.md`, qui détaille le modèle
« instance unique partagée ») : le raccourci Bureau/menu Démarrer de
l'utilisateur final pointe vers l'application cible elle-même (ex.
`Scrabble.exe`), jamais vers Actualise — c'est l'application cible qui, à
son propre démarrage, lance `Actualise.exe --config <nom>` par un
`Popen` non bloquant (sans attendre sa fin, sans bloquer sa propre
fenêtre), et seulement si `C:\Actualise\Actualise.exe` existe sur la
machine (sinon elle démarre normalement, sans mise à jour). Ce lancement
fait partie du code de l'application cible (voir INTEGRATION.md, §6) ;
Actualise n'a donc jamais besoin d'être lancé directement par
l'utilisateur, et ne lance lui-même aucune application cible.
