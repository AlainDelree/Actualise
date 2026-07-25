"""Tests unitaires pour ``mise_a_jour.py``.

Aucun appel réseau réel : les réponses HTTP sont simulées via
``unittest.mock``. Voir CONCEPTION.md, « Distribution des binaires »,
« Manifeste de mise à jour » et « Vérification SHA-256 du zip ».
"""

import hashlib
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from mise_a_jour import (
    appliquer_manifeste,
    extraire_zip,
    telecharger_zip,
    verifier_sha256,
)


class TestVerifierSha256(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.chemin_fichier = Path(self.dossier_temp.name) / "fichier.bin"
        self.chemin_fichier.write_bytes(b"contenu de test")
        self.hash_correct = hashlib.sha256(b"contenu de test").hexdigest()

    def test_hash_correct_retourne_true(self):
        self.assertTrue(verifier_sha256(self.chemin_fichier, self.hash_correct))

    def test_hash_incorrect_retourne_false(self):
        self.assertFalse(verifier_sha256(self.chemin_fichier, "0" * 64))

    def test_fichier_absent_retourne_false(self):
        chemin_absent = Path(self.dossier_temp.name) / "inexistant.bin"
        self.assertFalse(verifier_sha256(chemin_absent, self.hash_correct))


class TestTelechargerZip(unittest.TestCase):
    def _reponse_simulee(self, contenu: bytes) -> MagicMock:
        reponse = MagicMock()
        reponse.raise_for_status.return_value = None
        reponse.iter_content.return_value = [contenu]
        return reponse

    @patch("mise_a_jour.requests.get")
    def test_hash_valide_retourne_un_path_existant(self, mock_get):
        contenu = b"contenu du zip"
        hash_valide = hashlib.sha256(contenu).hexdigest()
        mock_get.return_value = self._reponse_simulee(contenu)

        resultat = telecharger_zip("https://example.invalid/maj.zip", hash_valide)

        try:
            self.assertIsNotNone(resultat)
            self.assertTrue(resultat.exists())
            self.assertEqual(resultat.read_bytes(), contenu)
        finally:
            if resultat is not None:
                resultat.unlink(missing_ok=True)

    @patch("mise_a_jour.requests.get")
    def test_hash_invalide_retourne_none_sans_fichier_residuel(self, mock_get):
        contenu = b"contenu du zip"
        mock_get.return_value = self._reponse_simulee(contenu)

        fichiers_avant = set(Path(tempfile.gettempdir()).glob("*.zip"))
        resultat = telecharger_zip("https://example.invalid/maj.zip", "0" * 64)
        fichiers_apres = set(Path(tempfile.gettempdir()).glob("*.zip"))

        self.assertIsNone(resultat)
        self.assertEqual(fichiers_avant, fichiers_apres)

    @patch("mise_a_jour.requests.get")
    def test_echec_reseau_retourne_none(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout

        resultat = telecharger_zip("https://example.invalid/maj.zip", "0" * 64)

        self.assertIsNone(resultat)


class TestExtraireZip(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)

    def _creer_zip(self, entrees: dict) -> Path:
        chemin_zip = Path(self.dossier_temp.name) / "source.zip"
        with zipfile.ZipFile(chemin_zip, "w") as archive:
            for nom, contenu in entrees.items():
                archive.writestr(nom, contenu)
        return chemin_zip

    def test_extraction_normale(self):
        chemin_zip = self._creer_zip({"a.txt": "A", "sous_dossier/b.txt": "B"})
        destination = Path(self.dossier_temp.name) / "destination"

        extraire_zip(chemin_zip, destination)

        self.assertEqual((destination / "a.txt").read_text(), "A")
        self.assertEqual((destination / "sous_dossier" / "b.txt").read_text(), "B")

    def test_zip_slip_leve_exception_et_extrait_rien_hors_destination(self):
        chemin_zip = self._creer_zip({"../evasion.txt": "malveillant"})
        destination = Path(self.dossier_temp.name) / "destination"

        with self.assertRaises(ValueError):
            extraire_zip(chemin_zip, destination)

        chemin_evasion = Path(self.dossier_temp.name) / "evasion.txt"
        self.assertFalse(chemin_evasion.exists())


class TestAppliquerManifeste(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.destination = Path(self.dossier_temp.name) / "destination"
        self.destination.mkdir()

    def test_suppression_effective_des_fichiers_listes(self):
        (self.destination / "obsolete.txt").write_text("ancien")
        manifest = {"supprimer": ["obsolete.txt"]}

        appliquer_manifeste(manifest, self.destination)

        self.assertFalse((self.destination / "obsolete.txt").exists())

    def test_chemin_absent_de_la_liste_non_touche(self):
        (self.destination / "conserve.txt").write_text("garder")
        manifest = {"supprimer": ["fichier_inexistant.txt"]}

        appliquer_manifeste(manifest, self.destination)

        self.assertTrue((self.destination / "conserve.txt").exists())

    def test_evasion_leve_exception_sans_rien_supprimer(self):
        (self.destination / "conserve.txt").write_text("garder")
        dossier_hors = Path(self.dossier_temp.name) / "fichier_hors_dossier"
        dossier_hors.write_text("ne doit pas être supprimé")
        manifest = {"supprimer": ["conserve.txt", "../fichier_hors_dossier"]}

        with self.assertRaises(ValueError):
            appliquer_manifeste(manifest, self.destination)

        self.assertTrue((self.destination / "conserve.txt").exists())
        self.assertTrue(dossier_hors.exists())


if __name__ == "__main__":
    unittest.main()
