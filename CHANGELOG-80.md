# Changelog — issue #80

## Issue #80 — Audit #92 : intégrité re-vérifiée à l'application et échec de vérification en fail-safe

- **SEC-022** : l'empreinte SHA-256 attendue (déjà connue au
  téléchargement, `version.json`) est désormais conservée dans un
  fichier sidecar `<zip>.sha256` à côté du zip en zone d'attente
  (`_chemin_empreinte_zip`, écrit par `tache_verification_arriere_plan`)
  et re-vérifiée juste avant application (`appliquer_mises_a_jour_en_attente`,
  via `mise_a_jour.verifier_sha256`). Un zip altéré sur le disque entre
  le téléchargement et le lancement suivant, ou sans sidecar (zip mis en
  attente par une version antérieure à ce correctif), n'est plus jamais
  appliqué : il est retiré de la zone d'attente (log d'une seule ligne)
  pour être retéléchargé — avec son empreinte, cette fois — au prochain
  contrôle.
- **SEC-025** : l'évasion de chemin (« zip slip ») détectée pendant
  l'extraction Python de l'auto-mise-à-jour d'Actualise
  (`mise_a_jour.extraire_zip`, appelée depuis
  `appliquer_mises_a_jour_en_attente`) levait une `ValueError` que seul
  un `except OSError` entourait : elle remontait jusqu'à planter le
  programme. Rattrapée désormais par un `except ValueError` dédié — saut
  propre, rien n'est appliqué, le zip (et son sidecar) est rejeté plutôt
  que rejoué à chaque lancement.
- **SEC-025** (chemin jeu) : l'extraction d'un zip de jeu se fait plus
  tard, par PowerShell (`Expand-Archive`) dans l'`updater.bat` généré,
  qui n'a pas la garde anti-évasion de `mise_a_jour.py`. Plutôt que de
  dupliquer cette garde en PowerShell, `mise_a_jour.py` expose
  désormais `valider_entrees_zip` (factorisée depuis `extraire_zip`,
  même garde `_verifier_chemin_dans_destination`, sans extraction) ;
  `_assurer_maj_jeu_en_attente` l'appelle avant même de générer/lancer
  le bat. Une évasion détectée : rien n'est généré ni appliqué, le zip
  est rejeté (retiré, pas rejoué au lancement suivant).
- **Tests ajoutés** (`tests/test_mise_a_jour.py`,
  `tests/test_actualise.py`) : `valider_entrees_zip` (entrées normales,
  évasion) ; zip en attente altéré (empreinte invalide, non appliqué,
  retiré) ; empreinte absente (non appliqué, retiré pour
  retéléchargement) ; évasion de chemin sur les deux chemins
  d'extraction — auto-mise-à-jour d'Actualise et mise à jour d'un jeu —
  avec vérification qu'aucune exception ne remonte et qu'il n'y a pas de
  rejeu au lancement suivant. Tous les tests existants adaptés pour
  créer le sidecar d'empreinte attendu par le nouveau contrôle (zip
  simulés comme s'ils venaient d'être téléchargés par la version
  corrigée).
- **CONCEPTION.md** : mise à jour des lignes « Vérification SHA-256 du
  zip » et ajout d'une ligne « Garde anti-évasion de chemin… » dans
  « Décisions actées » pour documenter les deux correctifs.
- **Hors périmètre, volontairement non traité** : authenticité par
  signature (SEC-023), risque accepté et consigné dans `.audit.json` ;
  découpage de `actualise.py`.
- **Important pour Alain** : ce correctif n'agit qu'à partir de la
  mise à jour *suivante* — voir le rapport de clôture de l'issue #80
  pour le détail et le protocole d'essai manuel à trois versions.
