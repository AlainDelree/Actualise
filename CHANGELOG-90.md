# Changelog — issue #90

## Issue #90 — Épingle les dépendances de requirements.txt et ajoute un test de garde

- `requirements.txt` : les 5 dépendances figées à une version exacte
  (`certifi==2026.10.23`, `charset-normalizer==3.5.2`, `idna==3.20`,
  `requests==2.34.2`, `urllib3==2.8.0`), pour builds reproductibles.
  Le fichier ne contenait auparavant que `requests==2.34.2` : aucune
  dépendance supplémentaire légitime trouvée.
- `tests/test_requirements.py` (nouveau) : lit `requirements.txt` et
  échoue si une ligne utile (hors vides/commentaires) n'est pas de la
  forme exacte `nom==version`, message d'échec citant la ligne fautive.
