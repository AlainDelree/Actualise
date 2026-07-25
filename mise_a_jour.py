"""Téléchargement, vérification SHA-256, extraction du zip de mise à
jour et application du manifeste.

Voir CONCEPTION.md, sections « Distribution des binaires — GitHub
Releases », « Manifeste de mise à jour » et « Séquence de démarrage —
vérification non bloquante » (étapes 3 et 4).
"""

import hashlib
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import requests

from version_check import TIMEOUT_RESEAU_SECONDES

_LOGGER = logging.getLogger(__name__)

# Taille des blocs de lecture/écriture, pour ne jamais charger un fichier
# (potentiellement volumineux) entièrement en mémoire.
_TAILLE_BLOC_OCTETS = 65536


def telecharger_zip(url: str, sha256_attendu: str) -> Path | None:
    """Télécharge le zip de mise à jour depuis ``url`` et vérifie son
    intégrité via ``sha256_attendu``.

    Voir CONCEPTION.md, « Séquence de démarrage » étape 3 : en cas de
    non-correspondance du SHA-256, le téléchargement est rejeté et
    aucune zone d'attente n'est mise à jour (même repli qu'un échec
    réseau). Retourne le chemin du zip téléchargé et validé, ou
    ``None`` en cas d'échec (réseau ou SHA-256 invalide).
    """
    fichier_temp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    chemin_temp = Path(fichier_temp.name)

    try:
        reponse = requests.get(url, timeout=TIMEOUT_RESEAU_SECONDES, stream=True)
        reponse.raise_for_status()
        with fichier_temp:
            for bloc in reponse.iter_content(chunk_size=_TAILLE_BLOC_OCTETS):
                fichier_temp.write(bloc)
    except requests.RequestException as erreur:
        _LOGGER.debug("Échec de téléchargement depuis %s : %s", url, erreur)
        chemin_temp.unlink(missing_ok=True)
        return None

    if not verifier_sha256(chemin_temp, sha256_attendu):
        _LOGGER.debug("SHA-256 invalide pour le zip téléchargé depuis %s", url)
        chemin_temp.unlink(missing_ok=True)
        return None

    return chemin_temp


def verifier_sha256(chemin_fichier: Path, hash_attendu: str) -> bool:
    """Calcule le SHA-256 de ``chemin_fichier`` et le compare à
    ``hash_attendu``.

    Voir CONCEPTION.md, « Format de version » (champ ``sha256`` du
    version.json) et « Vérification SHA-256 du zip » dans le tableau
    « Décisions actées ».
    """
    hachage = hashlib.sha256()
    try:
        with open(chemin_fichier, "rb") as f:
            for bloc in iter(lambda: f.read(_TAILLE_BLOC_OCTETS), b""):
                hachage.update(bloc)
    except OSError as erreur:
        _LOGGER.debug("Impossible de lire %s pour vérification SHA-256 : %s", chemin_fichier, erreur)
        return False

    return hachage.hexdigest() == hash_attendu


def _verifier_chemin_dans_destination(chemin_cible: Path, destination_resolue: Path) -> None:
    """Lève ``ValueError`` si ``chemin_cible`` (déjà résolu) s'évade de
    ``destination_resolue`` (protection anti « zip slip »).
    """
    if chemin_cible != destination_resolue and destination_resolue not in chemin_cible.parents:
        raise ValueError(
            f"Chemin d'évasion détecté hors de {destination_resolue} : {chemin_cible}"
        )


def extraire_zip(chemin_zip: Path, destination: Path) -> None:
    """Extrait ``chemin_zip`` dans ``destination``, en écrasant les
    fichiers existants de même nom et en ajoutant les nouveaux.

    Voir CONCEPTION.md, « Séquence de démarrage » étape 4, sous-étape 1
    (« extraction du zip »).
    """
    destination.mkdir(parents=True, exist_ok=True)
    destination_resolue = destination.resolve()

    with zipfile.ZipFile(chemin_zip) as archive:
        # Chaque chemin est validé avant toute extraction, pour ne
        # jamais écrire un seul fichier hors de ``destination`` même si
        # un membre plus loin dans l'archive s'avère malveillant
        # (pattern « zip slip » : ex. ``../../fichier``).
        for membre in archive.namelist():
            chemin_cible = (destination_resolue / membre).resolve()
            _verifier_chemin_dans_destination(chemin_cible, destination_resolue)

        archive.extractall(destination_resolue)


def appliquer_manifeste(manifest: dict[str, Any], destination: Path) -> None:
    """Applique le manifeste (``manifest.json``) après extraction :
    supprime les fichiers listés dans ``manifest["supprimer"]``.

    Liste noire optionnelle et fail-safe : seuls les chemins listés sont
    supprimés. Voir CONCEPTION.md, « Manifeste de mise à jour » et
    « Séquence de démarrage » étape 4, sous-étape 2.
    """
    destination_resolue = destination.resolve()

    # Deux passes : validation intégrale des chemins d'abord (même
    # protection anti-évasion que pour l'extraction), suppression
    # ensuite — un manifeste contenant un chemin d'évasion ne doit rien
    # supprimer du tout, pas seulement s'arrêter en cours de route.
    chemins_a_supprimer = []
    for chemin_relatif in manifest.get("supprimer", []):
        chemin_cible = (destination_resolue / chemin_relatif).resolve()
        _verifier_chemin_dans_destination(chemin_cible, destination_resolue)
        chemins_a_supprimer.append(chemin_cible)

    for chemin_cible in chemins_a_supprimer:
        if not chemin_cible.exists():
            _LOGGER.debug("Chemin du manifeste absent, ignoré : %s", chemin_cible)
            continue
        if chemin_cible.is_dir():
            shutil.rmtree(chemin_cible)
        else:
            chemin_cible.unlink()
