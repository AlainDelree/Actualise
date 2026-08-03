"""Tests unitaires pour ``config.py``.

Aucune modification de l'environnement réel de l'utilisateur : les
dossiers de configuration utilisés dans les tests sont systématiquement
des dossiers temporaires (``tempfile``), et ``sys.platform``/``os.environ``
sont simulés via ``unittest.mock``. Voir CONCEPTION.md, « Configuration
portable » et « Contenu de config.json ».
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import chemin_config_portable, charger_config, sauvegarder_config


class TestCheminConfigPortable(unittest.TestCase):
    @patch("config.os.environ", {"SYSTEMDRIVE": "D:"})
    @patch("config.sys.platform", "win32")
    def test_windows_non_fige_avec_systemdrive(self):
        # Mode script non figé (sys.frozen absent) : repli sur
        # l'ancien comportement, utile pour les tests/développement.
        self.assertEqual(chemin_config_portable(), Path("D:/Actualise"))

    @patch("config.os.environ", {})
    @patch("config.sys.platform", "win32")
    def test_windows_non_fige_sans_systemdrive_repli_sur_c(self):
        self.assertEqual(chemin_config_portable(), Path("C:/Actualise"))

    @patch("config.sys.executable", "D:/Apps/Actualise_Scrabble/Actualise.exe")
    @patch("config.sys.frozen", True, create=True)
    @patch("config.sys.platform", "win32")
    def test_windows_fige_pyinstaller_relatif_executable(self):
        # Mode PyInstaller figé : dossier contenant Actualise.exe,
        # résolu via sys.executable — pas un chemin fixe (voir
        # CONCEPTION.md, « Configuration portable »).
        self.assertEqual(
            chemin_config_portable(),
            Path("D:/Apps/Actualise_Scrabble"),
        )

    @patch(
        "config.sys.executable",
        "C:/Apps/Actualise_Rummikub/Actualise.exe",
    )
    @patch("config.sys.frozen", True, create=True)
    @patch("config.sys.platform", "win32")
    def test_windows_fige_pyinstaller_installations_independantes(self):
        # Deux installations distinctes (une par application cible)
        # résolvent vers des dossiers différents, sans collision.
        self.assertEqual(
            chemin_config_portable(),
            Path("C:/Apps/Actualise_Rummikub"),
        )

    @patch("config.os.environ", {"ACTUALISE_CONFIG_DIR": "/tmp/config-actualise-test"})
    @patch("config.sys.platform", "linux")
    def test_linux_avec_variable_environnement(self):
        self.assertEqual(
            chemin_config_portable(), Path("/tmp/config-actualise-test")
        )

    @patch("config.os.environ", {})
    @patch("config.sys.platform", "linux")
    def test_linux_sans_variable_environnement_repli_sur_home(self):
        self.assertEqual(
            chemin_config_portable(), Path.home() / ".config" / "actualise"
        )


class TestChargerConfig(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.chemin_dossier = Path(self.dossier_temp.name)
        patcher = patch("config.chemin_config_portable", return_value=self.chemin_dossier)
        self.mock_chemin = patcher.start()
        self.addCleanup(patcher.stop)

    def test_chargement_valide_retourne_le_dict(self):
        config_attendue = {"actualise": {"build_installe": 12}, "topic_ntfy": "actualise-scrabble"}
        (self.chemin_dossier / "config.json").write_text(
            json.dumps(config_attendue), encoding="utf-8"
        )

        self.assertEqual(charger_config(), config_attendue)

    def test_fichier_absent_leve_une_exception(self):
        with self.assertRaises(FileNotFoundError):
            charger_config()

    def test_json_invalide_leve_une_exception(self):
        (self.chemin_dossier / "config.json").write_text("{ceci n'est pas du json", encoding="utf-8")

        with self.assertRaises(json.JSONDecodeError):
            charger_config()


class TestSauvegarderConfig(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.chemin_dossier = Path(self.dossier_temp.name) / "sous_dossier" / "actualise"
        patcher = patch("config.chemin_config_portable", return_value=self.chemin_dossier)
        self.mock_chemin = patcher.start()
        self.addCleanup(patcher.stop)

    def test_aller_retour_avec_charger_config(self):
        config = {"actualise": {"build_installe": 12}, "topic_ntfy": "actualise-scrabble"}

        sauvegarder_config(config)

        self.assertEqual(charger_config(), config)

    def test_cree_le_dossier_parent_si_absent(self):
        self.assertFalse(self.chemin_dossier.exists())

        sauvegarder_config({"cle": "valeur"})

        self.assertTrue((self.chemin_dossier / "config.json").is_file())

    def test_aucun_fichier_temporaire_residuel(self):
        sauvegarder_config({"cle": "valeur"})

        fichiers = list(self.chemin_dossier.iterdir())
        self.assertEqual(fichiers, [self.chemin_dossier / "config.json"])


if __name__ == "__main__":
    unittest.main()
