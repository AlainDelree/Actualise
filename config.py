"""Lecture/écriture de config_actualise.json / config_<app>.json et
résolution du chemin de configuration portable (Windows/Linux).

Voir CONCEPTION.md, sections « Contenu de config.json » et
« Configuration portable ».
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

_NOM_FICHIER_ACTUALISE = "config_actualise.json"
_GABARIT_NOM_FICHIER_APP = "config_{nom}.json"


def chemin_config_portable() -> Path:
    """Retourne le chemin du dossier de configuration selon l'OS.

    Windows, mode PyInstaller figé (``sys.frozen`` vrai) : dossier
    contenant l'exécutable ``Actualise.exe`` lui-même, obtenu via
    ``sys.executable`` — et non un chemin Windows fixe. Ceci permet
    plusieurs installations indépendantes d'Actualise sur la même
    machine (une par application cible) sans qu'une installation
    n'écrase le ``config.json`` d'une autre (voir CONCEPTION.md,
    « Configuration portable »).

    Windows, mode script non figé (développement/tests, ``sys.frozen``
    absent ou faux) : repli sur l'ancien comportement,
    ``%SYSTEMDRIVE%\\Actualise\\`` — la variable d'environnement
    ``SYSTEMDRIVE`` est préférée à un ``C:`` en dur pour rester correct
    sur une installation où le disque système n'est pas ``C:`` ; à
    défaut de cette variable (cas anormal), repli sur ``C:``.

    Linux (et autres OS non Windows) : comportement inchangé — variable
    d'environnement ``ACTUALISE_CONFIG_DIR`` si définie, sinon
    ``~/.config/actualise/`` ; la problématique de collision
    multi-installations ne s'y pose pas de la même façon (voir
    CONCEPTION.md, « Configuration portable »).

    Ne crée pas le dossier — résolution de chemin uniquement (voir
    ``sauvegarder_config_actualise``/``sauvegarder_config_app`` pour la
    création).
    """
    if sys.platform == "win32":
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent

        lecteur_systeme = os.environ.get("SYSTEMDRIVE", "C:")
        return Path(f"{lecteur_systeme}/Actualise")

    dossier_env = os.environ.get("ACTUALISE_CONFIG_DIR")
    if dossier_env:
        return Path(dossier_env)

    return Path.home() / ".config" / "actualise"


def _nom_fichier_app(nom_app: str) -> str:
    return _GABARIT_NOM_FICHIER_APP.format(nom=nom_app)


def _charger_json(chemin_fichier: Path) -> dict[str, Any]:
    with open(chemin_fichier, encoding="utf-8-sig") as f:
        return json.load(f)


def _ecrire_json_atomique(chemin_fichier: Path, contenu: dict[str, Any]) -> None:
    """Écrit ``contenu`` en JSON dans ``chemin_fichier``, atomiquement.

    Crée le dossier de configuration si nécessaire. Écriture atomique :
    le contenu est d'abord écrit dans un fichier temporaire du même
    dossier, puis basculé via ``os.replace`` — un fichier temporaire
    partiellement écrit (interruption en cours de route) ne peut donc
    jamais remplacer un fichier de configuration déjà valide.
    """
    dossier_config = chemin_fichier.parent
    dossier_config.mkdir(parents=True, exist_ok=True)

    fichier_temp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=dossier_config,
        prefix=f".{chemin_fichier.name}.",
        suffix=".tmp",
        delete=False,
    )
    chemin_temp = Path(fichier_temp.name)
    try:
        with fichier_temp:
            json.dump(contenu, fichier_temp, indent=2, ensure_ascii=False)
        os.replace(chemin_temp, chemin_fichier)
    except BaseException:
        chemin_temp.unlink(missing_ok=True)
        raise


def charger_config(nom_app: str) -> dict[str, Any]:
    """Charge et fusionne config_actualise.json et config_<nom_app>.json.

    Voir CONCEPTION.md, section « Contenu de config.json », pour le
    format attendu. Retourne un dict compatible avec la structure
    utilisée par ``actualise.py`` :

    - ``actualise`` : contenu de config_actualise.json sans zone_attente
    - ``application_cible`` : contenu entier de config_<nom_app>.json
    - ``zone_attente`` : depuis config_actualise.json
    - ``topic_ntfy`` : copié depuis ``application_cible``, pour
      compatibilité avec l'appelant actuel

    L'absence de configuration valide est bloquante pour Actualise (à
    la différence de ``verifier_version``, pas de repli silencieux
    ici) : les exceptions standard ``FileNotFoundError`` (fichier
    absent) et ``json.JSONDecodeError`` (JSON malformé) sont laissées
    se propager telles quelles à l'appelant, plutôt que d'introduire
    une exception dédiée.
    """
    dossier_config = chemin_config_portable()

    config_actualise = _charger_json(dossier_config / _NOM_FICHIER_ACTUALISE)
    config_app = _charger_json(dossier_config / _nom_fichier_app(nom_app))

    zone_attente = config_actualise["zone_attente"]
    bloc_actualise = {cle: valeur for cle, valeur in config_actualise.items() if cle != "zone_attente"}

    return {
        "actualise": bloc_actualise,
        "application_cible": config_app,
        "zone_attente": zone_attente,
        "topic_ntfy": config_app["topic_ntfy"],
    }


def sauvegarder_config_actualise(bloc_actualise: dict[str, Any], zone_attente: str) -> None:
    """Sauvegarde config_actualise.json (build_installe Actualise,
    depot_github, zone_attente).

    Voir CONCEPTION.md, section « Contenu de config.json ».
    """
    contenu = {**bloc_actualise, "zone_attente": zone_attente}
    chemin_fichier = chemin_config_portable() / _NOM_FICHIER_ACTUALISE
    _ecrire_json_atomique(chemin_fichier, contenu)


def sauvegarder_config_app(nom_app: str, bloc_app: dict[str, Any]) -> None:
    """Sauvegarde config_<nom_app>.json (tous les champs
    application_cible).

    Voir CONCEPTION.md, section « Contenu de config.json ».
    """
    chemin_fichier = chemin_config_portable() / _nom_fichier_app(nom_app)
    _ecrire_json_atomique(chemin_fichier, bloc_app)
