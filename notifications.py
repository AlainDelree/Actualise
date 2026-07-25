"""Envoi de notifications ntfy.

Voir CONCEPTION.md, section « Contenu de config.json » (champ
``topic_ntfy``) et « Décisions actées » (« un topic ntfy dédié par
programme géré »).
"""


def notifier_ntfy(topic: str, message: str) -> None:
    """Envoie ``message`` sur le topic ntfy ``topic``.

    Utilisé notamment pour la notification informative envoyée quand une
    mise à jour a été téléchargée et validée en arrière-plan (voir
    CONCEPTION.md, « Séquence de démarrage » étape 3).
    """
    raise NotImplementedError
