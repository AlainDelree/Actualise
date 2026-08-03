"""Lecture/écriture de config.json et résolution du chemin de
configuration portable (Windows/Linux).

Voir CONCEPTION.md, sections « Contenu de config.json » et
« Configuration portable ».
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

_NOM_FICHIER_CONFIG = "config.json"


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
    ``sauvegarder_config`` pour la création).
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


def charger_config() -> dict[str, Any]:
    """Charge et retourne le contenu de config.json.

    Voir CONCEPTION.md, section « Contenu de config.json », pour le
    format attendu (blocs ``actualise`` / ``application_cible``,
    ``zone_attente``, ``topic_ntfy``).

    L'absence de configuration valide est bloquante pour Actualise (à
    la différence de ``verifier_version``, pas de repli silencieux
    ici) : les exceptions standard ``FileNotFoundError`` (fichier
    absent) et ``json.JSONDecodeError`` (JSON malformé) sont laissées
    se propager telles quelles à l'appelant, plutôt que d'introduire
    une exception dédiée.
    """
    chemin_fichier = chemin_config_portable() / _NOM_FICHIER_CONFIG
    with open(chemin_fichier, encoding="utf-8") as f:
        return json.load(f)


def sauvegarder_config(config: dict[str, Any]) -> None:
    """Écrit le contenu de ``config`` dans config.json.

    Voir CONCEPTION.md, section « Contenu de config.json ».

    Crée le dossier de configuration si nécessaire. Écriture atomique :
    le contenu est d'abord écrit dans un fichier temporaire du même
    dossier, puis basculé via ``os.replace`` — un fichier temporaire
    partiellement écrit (interruption en cours de route) ne peut donc
    jamais remplacer un ``config.json`` déjà valide.
    """
    dossier_config = chemin_config_portable()
    dossier_config.mkdir(parents=True, exist_ok=True)
    chemin_fichier = dossier_config / _NOM_FICHIER_CONFIG

    fichier_temp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=dossier_config,
        prefix=f".{_NOM_FICHIER_CONFIG}.",
        suffix=".tmp",
        delete=False,
    )
    chemin_temp = Path(fichier_temp.name)
    try:
        with fichier_temp:
            json.dump(config, fichier_temp, indent=2, ensure_ascii=False)
        os.replace(chemin_temp, chemin_fichier)
    except BaseException:
        chemin_temp.unlink(missing_ok=True)
        raise
