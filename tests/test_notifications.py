"""Tests unitaires pour ``notifications.py``.

Aucun appel réseau réel : les réponses HTTP sont simulées via
``unittest.mock``. Voir CONCEPTION.md, « Décisions actées » (repli
silencieux sur échec réseau).
"""

import unittest
from unittest.mock import MagicMock, patch

import requests

from notifications import notifier_ntfy


class TestNotifierNtfy(unittest.TestCase):
    @patch("notifications.requests.post")
    def test_envoi_reussi_appelle_post_avec_bonne_url_et_message(self, mock_post):
        reponse = MagicMock()
        reponse.raise_for_status.return_value = None
        mock_post.return_value = reponse

        notifier_ntfy("mon-topic", "un message")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://ntfy.sh/mon-topic")
        self.assertEqual(kwargs["data"], "un message".encode("utf-8"))

    @patch("notifications.requests.post")
    def test_timeout_reseau_ne_leve_pas_exception(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout

        notifier_ntfy("mon-topic", "un message")

    @patch("notifications.requests.post")
    def test_erreur_http_ne_leve_pas_exception(self, mock_post):
        reponse = MagicMock()
        reponse.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = reponse

        notifier_ntfy("mon-topic", "un message")


if __name__ == "__main__":
    unittest.main()
