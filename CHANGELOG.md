# Changelog — issue #57

# Changelog — issue #61

- Documentation (`CONCEPTION.md`, sections « Distribution des binaires —
  GitHub Releases » et « Décisions actées ») : correction du nommage
  d'asset documenté, qui décrivait un nom fixe sans numéro de version
  (`<préfixe>.zip`, réécrasé à chaque Release) alors que le code
  (`actualise.py::_url_asset_release`) construit et a toujours construit
  un nom versionné `<préfixe>-v<build>.zip` (ex. `actualise-v48.zip`,
  cohérent avec `_GABARIT_URL_RELEASE`). La documentation reflète
  désormais le comportement réel du code, avec l'explication du choix :
  cohérence avec le nommage déjà utilisé pour les applications cibles
  (ex. `Scrabble-Setup-v10.exe`), pas de dépendance à une URL « latest »
  puisque la publication reste pilotée manuellement par Alain. Aucun
  changement de code.

- Correction (`actualise.py`, `appliquer_mises_a_jour_en_attente`) : lecture
  de `manifest.json` extrait du zip en zone d'attente désormais décodée en
  `utf-8-sig` au lieu de `utf-8` strict, pour tolérer un BOM UTF-8 (InnoSetup
  peut écrire du JSON avec BOM, cf. issue #46 pour `config.py`). Corrige un
  crash au démarrage (`JSONDecodeError: Unexpected UTF-8 BOM`) confirmé en
  conditions réelles.
- Ajout d'un test de non-régression dans `tests/test_actualise.py`
  (`test_manifest_avec_bom_utf8_est_lu_correctement`), sur le modèle du test
  équivalent de `tests/test_config.py` pour l'issue #46.

