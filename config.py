"""Lecture/écriture de config.json et résolution du chemin de
configuration portable (Windows/Linux).

Voir CONCEPTION.md, sections « Contenu de config.json » et
« Configuration portable ».
"""

from pathlib import Path
from typing import Any


def chemin_config_portable() -> Path:
    """Retourne le chemin du dossier de configuration selon l'OS.

    Windows : ``C:\\Actualise\\``.
    Linux : ``~/.config/actualise/``, ou variable d'environnement dédiée
    si définie (voir CONCEPTION.md, « Configuration portable » et
    décision actée correspondante dans le tableau « Décisions actées »).
    """
    raise NotImplementedError


def charger_config() -> dict[str, Any]:
    """Charge et retourne le contenu de config.json.

    Voir CONCEPTION.md, section « Contenu de config.json », pour le
    format attendu (blocs ``actualise`` / ``application_cible``,
    ``zone_attente``, ``topic_ntfy``).
    """
    raise NotImplementedError


def sauvegarder_config(config: dict[str, Any]) -> None:
    """Écrit le contenu de ``config`` dans config.json.

    Voir CONCEPTION.md, section « Contenu de config.json ».
    """
    raise NotImplementedError
