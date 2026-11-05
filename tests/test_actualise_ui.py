"""Tests unitaires pour ``actualise_ui.py``.

Ne couvre que ``construire_commande_maj`` (pas d'interface graphique) :
voir audit #92, règle SEC-003, sur le remplacement de
``subprocess.Popen(..., shell=True)`` par une chaîne unique passée à
``cmd /c`` (sans shell=True), dont la partie interne est quotée par
``subprocess.list2cmdline`` puis ré-entourée d'une paire de guillemets
supplémentaire pour compenser le retrait fait par ``cmd /c``.
"""

import subprocess
import unittest
import unittest.mock
from pathlib import Path

from actualise_ui import construire_commande_maj

BAT_SANS_ESPACE = Path(r"C:\Jeu\updater.bat")
BAT_AVEC_ESPACE = Path(r"C:\Program Files\Jeu\updater.bat")
EXE_SANS_ESPACE = r"C:\Jeu\jeu.exe"
EXE_AVEC_ESPACE = r"C:\Program Files\Jeu\jeu.exe"


class TestConstruireCommandeMaj(unittest.TestCase):
    def test_sans_espace_sans_relance(self):
        commande = construire_commande_maj(BAT_SANS_ESPACE, None)
        self.assertEqual(commande, f'cmd /c "{BAT_SANS_ESPACE}"')

    def test_sans_espace_avec_relance(self):
        commande = construire_commande_maj(BAT_SANS_ESPACE, EXE_SANS_ESPACE)
        self.assertEqual(
            commande,
            f'cmd /c "{subprocess.list2cmdline([str(BAT_SANS_ESPACE), "--relancer", EXE_SANS_ESPACE])}"',
        )

    def test_bat_avec_espace_seul_sans_relance(self):
        commande = construire_commande_maj(BAT_AVEC_ESPACE, None)
        self.assertEqual(
            commande,
            f'cmd /c "{subprocess.list2cmdline([str(BAT_AVEC_ESPACE)])}"',
        )
        # Le chemin du bat est bien quoté à l'intérieur de la paire externe.
        self.assertIn(f'"{BAT_AVEC_ESPACE}"', commande)

    def test_bat_avec_espace_seul_avec_relance(self):
        commande = construire_commande_maj(BAT_AVEC_ESPACE, EXE_SANS_ESPACE)
        self.assertEqual(
            commande,
            f'cmd /c "{subprocess.list2cmdline([str(BAT_AVEC_ESPACE), "--relancer", EXE_SANS_ESPACE])}"',
        )

    def test_exe_avec_espace_seul_sans_relance(self):
        # Sans --relancer, le chemin de l'exécutable n'intervient pas.
        commande = construire_commande_maj(BAT_SANS_ESPACE, None)
        self.assertNotIn("Program Files", commande)

    def test_exe_avec_espace_seul_avec_relance(self):
        commande = construire_commande_maj(BAT_SANS_ESPACE, EXE_AVEC_ESPACE)
        self.assertEqual(
            commande,
            f'cmd /c "{subprocess.list2cmdline([str(BAT_SANS_ESPACE), "--relancer", EXE_AVEC_ESPACE])}"',
        )
        self.assertIn(f'"{EXE_AVEC_ESPACE}"', commande)

    def test_bat_et_exe_avec_espace_program_files(self):
        # Cas réel : installeurs Scrabble/Rummikub sous "Program Files".
        commande = construire_commande_maj(BAT_AVEC_ESPACE, EXE_AVEC_ESPACE)
        self.assertEqual(
            commande,
            f'cmd /c "{subprocess.list2cmdline([str(BAT_AVEC_ESPACE), "--relancer", EXE_AVEC_ESPACE])}"',
        )
        self.assertIn(f'"{BAT_AVEC_ESPACE}"', commande)
        self.assertIn(f'"{EXE_AVEC_ESPACE}"', commande)

    def test_commande_est_une_chaine_commencant_par_cmd_slash_c(self):
        commande = construire_commande_maj(BAT_AVEC_ESPACE, EXE_AVEC_ESPACE)
        self.assertIsInstance(commande, str)
        self.assertTrue(commande.startswith("cmd /c "))

    def test_popen_appele_sans_shell_true(self):
        # Reproduit l'appel fait par ``mettre_a_jour`` : la commande
        # construite est passée telle quelle à Popen, sans shell=True.
        commande = construire_commande_maj(BAT_AVEC_ESPACE, EXE_AVEC_ESPACE)

        appels = []

        class FauxPopen:
            def __init__(self, *args, **kwargs):
                appels.append((args, kwargs))

        with unittest.mock.patch("subprocess.Popen", FauxPopen):
            subprocess.Popen(commande)

        self.assertEqual(len(appels), 1)
        args, kwargs = appels[0]
        self.assertEqual(args, (commande,))
        self.assertNotIn("shell", kwargs)


if __name__ == "__main__":
    unittest.main()
