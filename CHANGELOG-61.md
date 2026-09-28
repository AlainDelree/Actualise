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
