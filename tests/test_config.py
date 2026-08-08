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

from config import (
    chemin_config_portable,
    charger_config,
    sauvegarder_config_actualise,
    sauvegarder_config_app,
)


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

    def _ecrire_config_actualise(self, contenu):
        (self.chemin_dossier / "config_actualise.json").write_text(
            json.dumps(contenu), encoding="utf-8"
        )

    def _ecrire_config_app(self, nom_app, contenu):
        (self.chemin_dossier / f"config_{nom_app}.json").write_text(
            json.dumps(contenu), encoding="utf-8"
        )

    def test_chargement_valide_fusionne_les_deux_fichiers(self):
        self._ecrire_config_actualise(
            {
                "build_installe": 6,
                "depot_github": "AlainDelree/Actualise",
                "zone_attente": "C:\\Actualise\\attente\\",
            }
        )
        self._ecrire_config_app(
            "scrabble",
            {
                "nom": "Scrabble",
                "depot_github": "AlainDelree/Scrabble",
                "build_installe": 5,
                "repertoire_installation": "C:\\Scrabble\\",
                "executable": "Scrabble.exe",
                "icone": "C:\\Scrabble\\Scrabble.ico",
                "topic_ntfy": "actualise-scrabble",
            },
        )

        self.assertEqual(
            charger_config("scrabble"),
            {
                "actualise": {
                    "build_installe": 6,
                    "depot_github": "AlainDelree/Actualise",
                },
                "application_cible": {
                    "nom": "Scrabble",
                    "depot_github": "AlainDelree/Scrabble",
                    "build_installe": 5,
                    "repertoire_installation": "C:\\Scrabble\\",
                    "executable": "Scrabble.exe",
                    "icone": "C:\\Scrabble\\Scrabble.ico",
                    "topic_ntfy": "actualise-scrabble",
                },
                "zone_attente": "C:\\Actualise\\attente\\",
                "topic_ntfy": "actualise-scrabble",
            },
        )

    def test_fichier_actualise_absent_leve_une_exception(self):
        self._ecrire_config_app("scrabble", {"topic_ntfy": "actualise-scrabble"})

        with self.assertRaises(FileNotFoundError):
            charger_config("scrabble")

    def test_fichier_app_absent_leve_une_exception(self):
        self._ecrire_config_actualise(
            {
                "build_installe": 6,
                "depot_github": "AlainDelree/Actualise",
                "zone_attente": "C:\\Actualise\\attente\\",
            }
        )

        with self.assertRaises(FileNotFoundError):
            charger_config("scrabble")

    def test_json_invalide_leve_une_exception(self):
        (self.chemin_dossier / "config_actualise.json").write_text(
            "{ceci n'est pas du json", encoding="utf-8"
        )

        with self.assertRaises(json.JSONDecodeError):
            charger_config("scrabble")


class TestSauvegarderConfigActualise(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.chemin_dossier = Path(self.dossier_temp.name) / "sous_dossier" / "actualise"
        patcher = patch("config.chemin_config_portable", return_value=self.chemin_dossier)
        self.mock_chemin = patcher.start()
        self.addCleanup(patcher.stop)

    def test_ecrit_le_bloc_actualise_et_la_zone_attente(self):
        sauvegarder_config_actualise(
            {"build_installe": 12, "depot_github": "AlainDelree/Actualise"},
            "/tmp/attente",
        )

        chemin_fichier = self.chemin_dossier / "config_actualise.json"
        self.assertEqual(
            json.loads(chemin_fichier.read_text(encoding="utf-8")),
            {
                "build_installe": 12,
                "depot_github": "AlainDelree/Actualise",
                "zone_attente": "/tmp/attente",
            },
        )

    def test_cree_le_dossier_parent_si_absent(self):
        self.assertFalse(self.chemin_dossier.exists())

        sauvegarder_config_actualise({"build_installe": 1}, "/tmp/attente")

        self.assertTrue((self.chemin_dossier / "config_actualise.json").is_file())

    def test_aucun_fichier_temporaire_residuel(self):
        sauvegarder_config_actualise({"build_installe": 1}, "/tmp/attente")

        fichiers = list(self.chemin_dossier.iterdir())
        self.assertEqual(fichiers, [self.chemin_dossier / "config_actualise.json"])


class TestSauvegarderConfigApp(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.chemin_dossier = Path(self.dossier_temp.name) / "sous_dossier" / "actualise"
        patcher = patch("config.chemin_config_portable", return_value=self.chemin_dossier)
        self.mock_chemin = patcher.start()
        self.addCleanup(patcher.stop)

    def test_ecrit_le_fichier_du_bon_nom(self):
        bloc_app = {
            "nom": "Scrabble",
            "depot_github": "AlainDelree/Scrabble",
            "build_installe": 5,
            "repertoire_installation": "C:\\Scrabble\\",
            "executable": "Scrabble.exe",
            "topic_ntfy": "actualise-scrabble",
        }

        sauvegarder_config_app("scrabble", bloc_app)

        chemin_fichier = self.chemin_dossier / "config_scrabble.json"
        self.assertEqual(json.loads(chemin_fichier.read_text(encoding="utf-8")), bloc_app)

    def test_cree_le_dossier_parent_si_absent(self):
        self.assertFalse(self.chemin_dossier.exists())

        sauvegarder_config_app("rummikub", {"cle": "valeur"})

        self.assertTrue((self.chemin_dossier / "config_rummikub.json").is_file())

    def test_aucun_fichier_temporaire_residuel(self):
        sauvegarder_config_app("rummikub", {"cle": "valeur"})

        fichiers = list(self.chemin_dossier.iterdir())
        self.assertEqual(fichiers, [self.chemin_dossier / "config_rummikub.json"])


class TestChargerConfigSauvegarderConfigAllerRetour(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.chemin_dossier = Path(self.dossier_temp.name)
        patcher = patch("config.chemin_config_portable", return_value=self.chemin_dossier)
        self.mock_chemin = patcher.start()
        self.addCleanup(patcher.stop)

    def test_aller_retour(self):
        sauvegarder_config_actualise(
            {"build_installe": 6, "depot_github": "AlainDelree/Actualise"},
            "/tmp/attente",
        )
        sauvegarder_config_app(
            "scrabble",
            {
                "nom": "Scrabble",
                "depot_github": "AlainDelree/Scrabble",
                "build_installe": 5,
                "repertoire_installation": "C:\\Scrabble\\",
                "executable": "Scrabble.exe",
                "topic_ntfy": "actualise-scrabble",
            },
        )

        configuration = charger_config("scrabble")

        self.assertEqual(configuration["actualise"]["build_installe"], 6)
        self.assertEqual(configuration["application_cible"]["nom"], "Scrabble")
        self.assertEqual(configuration["zone_attente"], "/tmp/attente")
        self.assertEqual(configuration["topic_ntfy"], "actualise-scrabble")


if __name__ == "__main__":
    unittest.main()
