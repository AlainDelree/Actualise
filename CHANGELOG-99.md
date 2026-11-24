# Changelog — issue #99

## Issue #99 — Corriger le commentaire sur les droits de `C:\` dans `installeur/actualise.iss`

Suite au signalement de l'issue #98 (laissé en l'état car #98
interdisait de toucher à ce fichier) : le commentaire précédant
`PrivilegesRequired=admin` dans `installeur/actualise.iss` affirmait à
tort que « C:\ est inaccessible en écriture aux utilisateurs standards »
et que l'admin serait requis pour cette raison. Corrigé pour s'aligner
sur `INTEGRATION.md` et `docs/contexte/integration_setup.md` : l'exigence
`admin` se justifie par l'incident réel constaté avec
`PrivilegesRequired=lowest` (les emplacements « tous les utilisateurs »
ne résolvent pas, Actualise n'est pas déployé), et non par une
protection de `C:\Actualise\` elle-même, qui reste sans règle de droits
posée par ce setup (SEC-022).

- `installeur/actualise.iss`, lignes 41-43 (avant) → 41-46 (après) :
  seul ce bloc de commentaire a changé, aucune directive/section/valeur
  du script — diff du fichier vide hors ces lignes de commentaire.

  Avant :
  ```
  ; C:\ est inaccessible en écriture aux utilisateurs standards ; admin est
  ; requis pour créer/écrire C:\Actualise\ (voir INTEGRATION.md, §3 "Droits
  ; d'installation" — incident réel documenté avec PrivilegesRequired=lowest).
  ```

  Après :
  ```
  ; admin est requis pour que les constantes InnoSetup "tous les
  ; utilisateurs" résolvent correctement (voir INTEGRATION.md, §3 "Droits
  ; d'installation" — incident réel documenté avec PrivilegesRequired=lowest :
  ; ces emplacements ne sont alors pas utilisés et Actualise n'est pas
  ; déployé). C:\Actualise\ lui-même n'est protégé par aucune règle de
  ; droits posée par ce setup (voir SEC-022 dans .audit.json).
  ```

Aucun nouveau build requis (commentaire seul). Aucun autre fichier
modifié.
