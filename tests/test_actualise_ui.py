"""Tests unitaires pour ``actualise_ui.py``.

Ne couvre que ``construire_commande_maj`` (pas d'interface graphique) :
voir audit #92, règle SEC-003, sur le remplacement de
``subprocess.Popen(..., shell=True)`` par un appel en liste via
``cmd /c``.
"""

import unittest
from pathlib import Path

from actualise_ui import construire_commande_maj


class TestConstruireCommandeMaj(unittest.TestCase):
    def test_sans_relance(self):
        commande = construire_commande_maj(Path(r"C:\Program Files\Jeu\updater.bat"), None)
        self.assertEqual(
            commande,
            ["cmd", "/c", str(Path(r"C:\Program Files\Jeu\updater.bat"))],
        )

    def test_avec_relance(self):
        commande = construire_commande_maj(
            Path(r"C:\Program Files\Jeu\updater.bat"),
            r"C:\Program Files\Jeu\jeu.exe",
        )
        self.assertEqual(
            commande,
            [
                "cmd",
                "/c",
                str(Path(r"C:\Program Files\Jeu\updater.bat")),
                "--relancer",
                r"C:\Program Files\Jeu\jeu.exe",
            ],
        )

    def test_pas_de_shell_string_assemblee(self):
        # La commande est une liste d'arguments, jamais une chaîne unique
        # susceptible d'être réinterprétée par un shell.
        commande = construire_commande_maj(Path("updater.bat"), None)
        self.assertIsInstance(commande, list)
        for element in commande:
            self.assertIsInstance(element, str)


if __name__ == "__main__":
    unittest.main()
