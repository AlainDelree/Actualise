# Changelog — issue #96

## Issue #96 — Restructurer CONTEXTE.md : 9 fichiers de domaine sous docs/contexte/

- Création de `docs/contexte/` et des 9 fichiers de domaine demandés,
  chacun migré depuis les sections correspondantes de l'ancien
  `CONTEXTE.md` (905 lignes, 62 524 caractères) : `vue_ensemble.md`,
  `versioning.md`, `distribution_releases.md`, `configuration.md`,
  `demarrage_reseau.md`, `bascule_mise_a_jour.md`,
  `actualiseui_dialogue.md`, `maj_application_cible.md`,
  `integration_setup.md`.
- Suppression de la table « Décisions actées » (table supprimée en tant
  que telle) : 4 lignes non dupliquées rapatriées dans
  `bascule_mise_a_jour.md` (vérification SHA-256 à l'application/sidecar
  SEC-022, limite connue zip non re-contrôlé #92, garde zip-slip
  SEC-025, Bootstrap séparé écarté) ; la ligne « Configuration »
  (modèle à fichier `config.json` unique) était fausse — supprimée sans
  migration ; les 20 autres lignes supprimées car déjà couvertes par
  leur fichier de domaine de destination (vérifié ligne par ligne).
- Suppression des récits datés/numérotés d'issues demandée par
  l'issue : paragraphe « Historique » en tête de la configuration
  (#3/#4/#7/#35), récit « instances séparées vers instance unique »
  (#27/#35/#36/#44/#54) des « Points de vigilance », récit « Un
  incident réel en production... »/« Correction (issue #73)... » du
  garde-fou anti-boucle, « Module ajouté (issue #36)... », cadrage
  narratif de la généralisation (#72/#73/#84/#92), paragraphe
  « Historique : voir Points de vigilance... » de l'intégration setup.
  Seule la règle résultante a été conservée dans chaque cas. Par la
  même logique (état actuel, jamais l'historique), suppression
  également du premier item de « Points de vigilance connus »
  (incident à l'origine de la configuration portable) : pur récit
  historique, redondant avec la description déjà présente dans
  « Configuration portable ».
- Correction de la mention périmée « à préciser côté implémentation »
  dans `distribution_releases.md` (cas `manifest.json` absent) : le
  comportement est désormais affirmé (nouvelle tentative au prochain
  cycle de vérification en arrière-plan).
- Redaction de la valeur sensible : le nom de topic de notification
  utilisé comme exemple dans la configuration (`config_<nom_app>.json`)
  a été remplacé par le nom factice `<topic-ntfy>` dans
  `docs/contexte/configuration.md` ; confirmé absent de tout fichier du
  dépôt après rédaction (une seule occurrence trouvée, dans l'ancien
  `CONTEXTE.md`, disparue avec sa réécriture).
- Réécriture de `CONTEXTE.md` (3101 caractères, structure imposée :
  Règles invariantes, Architecture, Conventions de nommage, Index des
  fichiers de domaine, renvoi README.md/INTEGRATION.md) avec une ligne
  d'index par fichier de domaine créé.
- Ajustement des renvois internes (« voir « X » ci-dessus/ci-dessous »)
  devenus incorrects du fait de l'éclatement en plusieurs fichiers : ils
  pointent désormais explicitement vers le fichier `docs/contexte/...`
  concerné plutôt que vers une section locale qui n'existe plus dans le
  même fichier. Les renvois « voir CONTEXTE.md, section X » présents
  dans d'autres fichiers (INTEGRATION.md, README.md, ETAT.md) n'ont pas
  été touchés (hors périmètre, laissés à une issue suivante).
