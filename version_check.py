"""Vérification de version.json (Actualise et application cible).

Voir CONCEPTION.md, sections « Format de version », « Deux fichiers
version.json distincts » et « Vérification réseau — timeout strict ».
"""

from typing import Any

# Timeout strict (2 à 3 secondes) sur toute requête réseau de
# vérification de version. Au-delà, la vérification est traitée comme
# un échec réseau et on se rabat silencieusement sur la version
# installée (voir CONCEPTION.md, « Vérification réseau — timeout
# strict » et « Décisions actées »).
TIMEOUT_RESEAU_SECONDES = 3


def verifier_version(depot_github: str, build_installe: int) -> dict[str, Any] | None:
    """Vérifie si une nouvelle version est disponible pour ``depot_github``.

    Récupère le version.json distant (``{"build": N, "sha256": "..."}``,
    voir CONCEPTION.md « Format de version ») avec le timeout strict
    ``TIMEOUT_RESEAU_SECONDES``, et le compare à ``build_installe``.

    Retourne le version.json distant si une nouvelle version est
    disponible (``distant.build > build_installe``), sinon ``None``
    (pas de mise à jour, ou échec réseau/timeout — repli silencieux,
    voir CONCEPTION.md « Décisions actées »).
    """
    raise NotImplementedError
