# Changelog — issue #100

## Issue #100 — Audit #117 (EXP-001) : mettre à jour les épingles `certifi` et `charset-normalizer`

Suite à l'audit #117 (règle EXP-001) qui signalait deux dépendances en
retard dans `requirements.txt` : mise à jour des épingles vers les
versions disponibles sur PyPI relevées par Alain le jour de l'audit.

- `requirements.txt`, lignes 1-2 :
  - `certifi==2026.10.23` → `certifi==2026.11.20`
  - `charset-normalizer==3.5.2` → `charset-normalizer==3.5.3`
  - Les trois autres épingles (`idna==3.20`, `requests==2.34.2`,
    `urllib3==2.8.0`) inchangées, format et ordre des lignes conservés.
- `tests/test_requirements.py` : non modifié, le test ne vérifie qu'un
  format générique (`nom==version` par regex), sans version en dur.
- Compatibilité vérifiée sans rien installer : les métadonnées déjà
  présentes sur la machine pour `requests==2.34.2` déclarent
  `charset_normalizer<4,>=2` et `certifi>=2023.5.7` — les deux nouvelles
  versions respectent ces contraintes.
- Ces épingles ne prennent effet dans l'exécutable qu'au prochain build
  publié d'Actualise, que seul Alain déclenche.
