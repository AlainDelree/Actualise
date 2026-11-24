# Changelog — issue #98

## Issue #98 — Documentation : `C:\Actualise` est modifiable par tous les utilisateurs locaux (corriger la doc et SEC-022)

Un diagnostic avait relevé (via `icacls C:\Actualise` sur une machine
réelle) que le dossier est modifiable en écriture par tous les
utilisateurs locaux, alors que la documentation affirmait le
contraire. L'installeur d'Actualise (`installeur/actualise.iss`) a été
relu : il ne pose aucune règle de droits sur `C:\Actualise\` (pas de
`Permissions:` dans `[Dirs]`, pas de commande `icacls`). Décision
assumée : garder ce comportement, car une mise à jour lancée depuis un
compte standard doit continuer de fonctionner sur un PC familial.

- `INTEGRATION.md` (puce « Droits d'installation ») : ne dit plus que
  `C:\Actualise\` est « inaccessible en écriture aux utilisateurs
  standards » du fait de la racine du disque système ; précise
  désormais que le dossier n'est protégé par aucune règle posée par le
  setup et reste modifiable par tous les utilisateurs locaux, avec
  renvoi vers `.audit.json` (SEC-022).
- `docs/contexte/integration_setup.md` : ne dit plus le dossier « fixe
  et non modifiable par l'utilisateur » ni la racine du disque système
  « inaccessible en écriture aux utilisateurs standards » ; même
  correction, `PrivilegesRequired=admin` et sa justification
  (constantes « tous les utilisateurs », incident réel avec `lowest`)
  conservées intactes.
- `.audit.json` : réécriture du seul texte `raison` de l'exception
  SEC-022 — ne cite plus « l'installeur de Scrabble » (non vérifié)
  mais les droits par défaut hérités de la racine du disque système
  plus une entrée explicite pour le groupe « Utilisateurs », sans
  aucune règle posée par le setup d'Actualise ; risque accepté sur un
  PC familial car une mise à jour sous compte standard doit continuer
  de fonctionner. Date d'origine conservée, date du jour ajoutée,
  mention « À revoir en même temps que SEC-023 » conservée. SEC-023 et
  le reste du fichier non touchés ; JSON vérifié valide.

Non corrigé volontairement : `installeur/actualise.iss` (commentaire
ligne 41, « C:\ est inaccessible en écriture aux utilisateurs
standards ») contient la même affirmation inexacte, mais la tâche
demandait explicitement de ne rien modifier dans ce fichier
(vérification en lecture seule uniquement). À traiter dans une issue
ultérieure si Alain le souhaite.
