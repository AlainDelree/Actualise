"""Envoi de notifications ntfy.

Voir docs/contexte/configuration.md, section « Contenu des fichiers de
configuration — `config_actualise.json` / `config_<nom_app>.json` »
(champ ``topic_ntfy``, règle « un topic ntfy dédié par programme géré »).
"""

import logging

import requests

from version_check import TIMEOUT_VERSION_SECONDES

_LOGGER = logging.getLogger(__name__)

_GABARIT_URL_NTFY = "https://ntfy.sh/{topic}"


def notifier_ntfy(topic: str, message: str) -> None:
    """Envoie ``message`` sur le topic ntfy ``topic``.

    Utilisé notamment pour la notification informative envoyée quand une
    mise à jour a été téléchargée et validée en arrière-plan (voir
    docs/contexte/demarrage_reseau.md, « Séquence de démarrage » étape 3).

    Repli silencieux en cas d'échec (timeout, connexion refusée, erreur
    HTTP) : une notification ratée ne doit jamais interrompre le flux
    normal d'Actualise (voir docs/contexte/demarrage_reseau.md,
    « Vérification réseau — timeout strict »).
    """
    url = _GABARIT_URL_NTFY.format(topic=topic)

    try:
        reponse = requests.post(url, data=message.encode("utf-8"), timeout=TIMEOUT_VERSION_SECONDES)
        reponse.raise_for_status()
    except requests.RequestException as erreur:
        _LOGGER.warning("Échec d'envoi de notification ntfy sur %s : %s", topic, erreur)
