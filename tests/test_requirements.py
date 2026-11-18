"""Tests unitaires pour ``requirements.txt``.

Garde-fou de reproductibilité des builds : chaque dépendance doit être
épinglée à une version exacte (``nom==version``), sans quoi deux builds
faits à des dates différentes peuvent embarquer des versions différentes.
Voir issue #90. N'installe rien : lecture du fichier texte seulement.
"""

import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
LIGNE_EPINGLEE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*==[A-Za-z0-9][A-Za-z0-9_.!+-]*$")


class TestRequirementsEpingles(unittest.TestCase):
    def test_chaque_ligne_utile_est_epinglee_a_une_version_exacte(self):
        contenu = (RACINE / "requirements.txt").read_text(encoding="utf-8")

        for ligne in contenu.splitlines():
            ligne_utile = ligne.strip()
            if not ligne_utile or ligne_utile.startswith("#"):
                continue
            self.assertRegex(
                ligne_utile,
                LIGNE_EPINGLEE,
                msg=(
                    f"requirements.txt : la ligne {ligne_utile!r} n'est pas "
                    "épinglée au format nom==version"
                ),
            )


if __name__ == "__main__":
    unittest.main()
