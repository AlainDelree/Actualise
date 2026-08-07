"""Vérification de version.json (Actualise et application cible).

Voir CONCEPTION.md, sections « Format de version », « Deux fichiers
version.json distincts » et « Vérification réseau — timeout strict ».
"""

import logging
from typing import Any

import requests

# Timeout strict sur les requêtes réseau légères de vérification de
# version (version.json) et de notification (ntfy). Au-delà, la
# vérification est traitée comme un échec réseau et on se rabat
# silencieusement sur la version installée (voir CONCEPTION.md,
# « Vérification réseau — timeout strict » et « Décisions actées »).
TIMEOUT_VERSION_SECONDES = 5

# Timeout distinct, plus généreux, pour le téléchargement du zip de
# mise à jour (potentiellement 30-80 Mo via GitHub Releases, avec au
# moins une redirection vers un CDN) — un timeout de quelques secondes
# à peine est inadapté à ce volume de données (voir issue #31).
TIMEOUT_DOWNLOAD_SECONDES = 60

_LOGGER = logging.getLogger(__name__)

# ``HEAD`` est une référence spéciale reconnue par raw.githubusercontent.com
# qui résout toujours vers la branche par défaut du dépôt, sans avoir à la
# connaître à l'avance ni à passer par l'API GitHub (voir CONCEPTION.md,
# « Deux fichiers version.json distincts »).
_GABARIT_URL_VERSION_JSON = "https://raw.githubusercontent.com/{depot}/HEAD/version.json"


def verifier_version(depot_github: str, build_installe: int) -> dict[str, Any] | None:
    """Vérifie si une nouvelle version est disponible pour ``depot_github``.

    Récupère le version.json distant (``{"build": N, "sha256": "..."}``,
    voir CONCEPTION.md « Format de version ») avec le timeout strict
    ``TIMEOUT_VERSION_SECONDES``, et le compare à ``build_installe``.

    Retourne le version.json distant si une nouvelle version est
    disponible (``distant.build > build_installe``), sinon ``None``
    (pas de mise à jour, ou échec réseau/timeout — repli silencieux,
    voir CONCEPTION.md « Décisions actées »).
    """
    url = _GABARIT_URL_VERSION_JSON.format(depot=depot_github)

    try:
        reponse = requests.get(url, timeout=TIMEOUT_VERSION_SECONDES)
        reponse.raise_for_status()
        distant = reponse.json()
    except (requests.RequestException, ValueError) as erreur:
        _LOGGER.warning("Échec de vérification de version pour %s : %s", depot_github, erreur)
        return None

    try:
        build_distant = distant["build"]
    except (KeyError, TypeError) as erreur:
        _LOGGER.warning("version.json invalide pour %s : %s", depot_github, erreur)
        return None

    # Comparaison entière stricte — jamais de comparaison de chaînes
    # (voir CONCEPTION.md, piège « "9" > "10" » lexicographique).
    if int(build_distant) > build_installe:
        return distant

    return None
