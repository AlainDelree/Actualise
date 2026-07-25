"""Envoi de notifications ntfy.

Voir CONCEPTION.md, section « Contenu de config.json » (champ
``topic_ntfy``) et « Décisions actées » (« un topic ntfy dédié par
programme géré »).
"""

import logging

import requests

from version_check import TIMEOUT_RESEAU_SECONDES

_LOGGER = logging.getLogger(__name__)

_GABARIT_URL_NTFY = "https://ntfy.sh/{topic}"


def notifier_ntfy(topic: str, message: str) -> None:
    """Envoie ``message`` sur le topic ntfy ``topic``.

    Utilisé notamment pour la notification informative envoyée quand une
    mise à jour a été téléchargée et validée en arrière-plan (voir
    CONCEPTION.md, « Séquence de démarrage » étape 3).

    Repli silencieux en cas d'échec (timeout, connexion refusée, erreur
    HTTP) : une notification ratée ne doit jamais interrompre le flux
    normal d'Actualise (voir CONCEPTION.md, « Décisions actées »).
    """
    url = _GABARIT_URL_NTFY.format(topic=topic)

    try:
        reponse = requests.post(url, data=message.encode("utf-8"), timeout=TIMEOUT_RESEAU_SECONDES)
        reponse.raise_for_status()
    except requests.RequestException as erreur:
        _LOGGER.debug("Échec d'envoi de notification ntfy sur %s : %s", topic, erreur)
