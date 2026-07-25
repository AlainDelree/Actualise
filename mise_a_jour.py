"""Téléchargement, vérification SHA-256, extraction du zip de mise à
jour et application du manifeste.

Voir CONCEPTION.md, sections « Distribution des binaires — GitHub
Releases », « Manifeste de mise à jour » et « Séquence de démarrage —
vérification non bloquante » (étapes 3 et 4).
"""

from pathlib import Path
from typing import Any


def telecharger_zip(url: str, sha256_attendu: str) -> Path | None:
    """Télécharge le zip de mise à jour depuis ``url`` et vérifie son
    intégrité via ``sha256_attendu``.

    Voir CONCEPTION.md, « Séquence de démarrage » étape 3 : en cas de
    non-correspondance du SHA-256, le téléchargement est rejeté et
    aucune zone d'attente n'est mise à jour (même repli qu'un échec
    réseau). Retourne le chemin du zip téléchargé et validé, ou
    ``None`` en cas d'échec (réseau ou SHA-256 invalide).
    """
    raise NotImplementedError


def verifier_sha256(chemin_fichier: Path, hash_attendu: str) -> bool:
    """Calcule le SHA-256 de ``chemin_fichier`` et le compare à
    ``hash_attendu``.

    Voir CONCEPTION.md, « Format de version » (champ ``sha256`` du
    version.json) et « Vérification SHA-256 du zip » dans le tableau
    « Décisions actées ».
    """
    raise NotImplementedError


def extraire_zip(chemin_zip: Path, destination: Path) -> None:
    """Extrait ``chemin_zip`` dans ``destination``, en écrasant les
    fichiers existants de même nom et en ajoutant les nouveaux.

    Voir CONCEPTION.md, « Séquence de démarrage » étape 4, sous-étape 1
    (« extraction du zip »).
    """
    raise NotImplementedError


def appliquer_manifeste(manifest: dict[str, Any], destination: Path) -> None:
    """Applique le manifeste (``manifest.json``) après extraction :
    supprime les fichiers listés dans ``manifest["supprimer"]``.

    Liste noire optionnelle et fail-safe : seuls les chemins listés sont
    supprimés. Voir CONCEPTION.md, « Manifeste de mise à jour » et
    « Séquence de démarrage » étape 4, sous-étape 2.
    """
    raise NotImplementedError
