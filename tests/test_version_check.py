"""Tests unitaires pour ``verifier_version`` (version_check.py).

Aucun appel réseau réel : les réponses HTTP sont simulées via
``unittest.mock``. Voir CONCEPTION.md, « Format de version » et
« Vérification réseau — timeout strict ».
"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from version_check import verifier_version


class TestVerifierVersion(unittest.TestCase):
    @patch("version_check.requests.get")
    def test_build_superieur_retourne_le_dict_complet(self, mock_get):
        reponse_simulee = MagicMock()
        reponse_simulee.json.return_value = {"build": 48, "sha256": "abc123"}
        mock_get.return_value = reponse_simulee

        resultat = verifier_version("owner/repo", build_installe=47)

        self.assertEqual(resultat, {"build": 48, "sha256": "abc123"})

    @patch("version_check.requests.get")
    def test_build_inferieur_ou_egal_retourne_none(self, mock_get):
        reponse_simulee = MagicMock()
        reponse_simulee.json.return_value = {"build": 47, "sha256": "abc123"}
        mock_get.return_value = reponse_simulee

        resultat = verifier_version("owner/repo", build_installe=47)

        self.assertIsNone(resultat)

    @patch("version_check.requests.get")
    def test_timeout_reseau_retourne_none_sans_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout

        resultat = verifier_version("owner/repo", build_installe=47)

        self.assertIsNone(resultat)

    @patch("version_check.requests.get")
    def test_json_invalide_retourne_none_sans_exception(self, mock_get):
        reponse_simulee = MagicMock()
        reponse_simulee.json.side_effect = ValueError("JSON invalide")
        mock_get.return_value = reponse_simulee

        resultat = verifier_version("owner/repo", build_installe=47)

        self.assertIsNone(resultat)


if __name__ == "__main__":
    unittest.main()
