#!/usr/bin/env python3
"""Point d'entrée principal d'Actualise.

Voir CONCEPTION.md, section « Séquence de démarrage — vérification non
bloquante » pour le déroulé complet, et « Garde-fou anti-boucle
infinie » pour le rôle de l'argument ``--child``.
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path

import config
import mise_a_jour
import notifications
import version_check

_LOGGER = logging.getLogger(__name__)

# Gabarit de l'URL d'un asset de Release GitHub (voir CONCEPTION.md,
# « Distribution des binaires — GitHub Releases »). Le numéro de build
# sert directement de tag (ex. ``v48``) : simple, lisible, et cohérent
# avec l'entier incrémental déjà acté comme identifiant de version
# (voir « Format de version ») — à documenter/adapter si un autre
# format de tag devait un jour être retenu.
_GABARIT_URL_RELEASE = "https://github.com/{depot}/releases/download/v{build}/{fichier}"


def analyser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Définit et analyse les arguments de la ligne de commande.

    ``--child`` est le marqueur explicite parent → enfant du garde-fou
    anti-boucle infinie (voir CONCEPTION.md, « Garde-fou anti-boucle
    infinie ») : si présent, l'instance saute inconditionnellement toute
    bascule d'auto-mise-à-jour supplémentaire.
    """
    analyseur = argparse.ArgumentParser(description="Actualise — mise à jour automatique")
    analyseur.add_argument(
        "--child",
        action="store_true",
        help="Marqueur interne : instance relancée après bascule d'auto-mise-à-jour (voir CONCEPTION.md)",
    )
    return analyseur.parse_args(argv)


def _prefixe_pour(nom: str) -> str:
    """Dérive le préfixe de nommage en zone d'attente à partir du nom
    d'un programme (ex. ``"Scrabble"`` → ``"scrabble"``).

    Voir CONCEPTION.md, « Nommage versionné des zips en zone d'attente »
    (ex. ``scrabble_112.zip`` pour un ``config["application_cible"]["nom"]``
    valant ``"Scrabble"``).
    """
    return nom.lower()


def _chercher_zip_en_attente(zone_attente: Path, prefixe: str) -> tuple[Path, int] | None:
    """Cherche dans ``zone_attente`` un fichier ``<prefixe>_<build>.zip``.

    Retourne son chemin et le ``build`` extrait du nom de fichier, ou
    ``None`` si aucun fichier de ce préfixe n'est présent (y compris si
    ``zone_attente`` lui-même n'existe pas encore, cas du tout premier
    lancement). Voir CONCEPTION.md, « Nommage versionné des zips en zone
    d'attente ».

    **Cas limite : plusieurs zips du même préfixe.** Seul celui au build
    le plus élevé est retourné ; tous les autres sont des résidus
    dépassés (voir CONCEPTION.md, cas limite dédié) et sont supprimés
    immédiatement ici même, sans être appliqués — ce choix
    d'implémentation garde l'appelant simple (il ne reçoit jamais qu'un
    seul candidat à traiter).
    """
    if not zone_attente.is_dir():
        return None

    motif = re.compile(rf"^{re.escape(prefixe)}_(\d+)\.zip$")
    candidats = []
    for chemin in zone_attente.iterdir():
        correspondance = motif.match(chemin.name)
        if correspondance:
            candidats.append((chemin, int(correspondance.group(1))))

    if not candidats:
        return None

    candidats.sort(key=lambda candidat: candidat[1], reverse=True)
    meilleur, *residus = candidats
    for chemin_residu, _ in residus:
        chemin_residu.unlink()

    return meilleur


def _relancer_en_enfant() -> None:
    """Relance une 2ème instance d'Actualise avec le marqueur ``--child``.

    Voir CONCEPTION.md, « Garde-fou anti-boucle infinie ». Gère aussi
    bien le cas d'un exécutable PyInstaller gelé (``sys.frozen``) que
    l'exécution directe du script Python.
    """
    if getattr(sys, "frozen", False):
        commande = [sys.executable, "--child"]
    else:
        commande = [sys.executable, str(Path(__file__).resolve()), "--child"]

    subprocess.Popen(commande)


def _basculer_par_renommage(dossier_source: Path, destination: Path) -> None:
    """Bascule le contenu de ``dossier_source`` (dossier temporaire
    d'extraction) vers ``destination``, fichier par fichier, via
    renommage (``os.replace``) plutôt qu'une réécriture en place.

    Un ``.exe`` en cours d'exécution ne peut pas être réécrit en place
    sous Windows (``PermissionError``), mais peut être renommé — voir
    CONCEPTION.md, « Garde-fou anti-boucle infinie ». Toute ``OSError``
    (ex. fichier encore verrouillé) remonte telle quelle à l'appelant,
    qui décide de la marche à suivre (conservation du zip source pour
    nouvelle tentative).
    """
    for chemin_source in dossier_source.rglob("*"):
        chemin_relatif = chemin_source.relative_to(dossier_source)
        chemin_destination = destination / chemin_relatif
        if chemin_source.is_dir():
            chemin_destination.mkdir(parents=True, exist_ok=True)
        else:
            chemin_destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(chemin_source, chemin_destination)


def appliquer_mises_a_jour_en_attente(est_enfant: bool) -> None:
    """Applique, au lancement, les mises à jour mises en attente au
    cycle précédent (étape 4 de la séquence de démarrage).

    Si ``est_enfant`` est vrai (marqueur ``--child`` présent), cette
    étape est sautée inconditionnellement pour Actualise lui-même — voir
    CONCEPTION.md, « Garde-fou anti-boucle infinie ».
    """
    if est_enfant:
        return

    configuration = config.charger_config()

    try:
        zone_attente = Path(configuration["zone_attente"])

        cibles = [
            ("actualise", configuration["actualise"], config.chemin_config_portable()),
            (
                _prefixe_pour(configuration["application_cible"]["nom"]),
                configuration["application_cible"],
                Path(configuration["application_cible"]["repertoire_installation"]),
            ),
        ]

        for prefixe, bloc_config, repertoire_installation in cibles:
            resultat = _chercher_zip_en_attente(zone_attente, prefixe)
            if resultat is None:
                continue

            chemin_zip, build_zip = resultat

            if build_zip <= bloc_config["build_installe"]:
                # Résidu obsolète (déjà appliqué à un cycle précédent, ou
                # périmé) : nettoyage automatique sans bascule, voir
                # CONCEPTION.md « Nommage versionné des zips en zone
                # d'attente ».
                chemin_zip.unlink()
                continue

            try:
                with zipfile.ZipFile(chemin_zip) as archive:
                    manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except zipfile.BadZipFile:
                # Zip corrompu ou pas un zip valide : bloquant, même
                # traitement qu'un manifeste absent ci-dessous — voir
                # CONCEPTION.md, « Manifeste de mise à jour », cas
                # limite dédié.
                _LOGGER.warning(
                    "Zip de mise à jour invalide en zone d'attente (%s) : "
                    "bascule ignorée, zip conservé pour nouvelle tentative.",
                    chemin_zip,
                )
                continue
            except KeyError:
                # manifest.json absent de l'archive : traité comme
                # bloquant, zip conservé pour nouvelle tentative
                # ultérieure — voir CONCEPTION.md, « Manifeste de mise
                # à jour », cas limite dédié.
                _LOGGER.warning(
                    "manifest.json absent du zip de mise à jour (%s) : "
                    "bascule ignorée, zip conservé pour nouvelle tentative.",
                    chemin_zip,
                )
                continue

            if prefixe == "actualise":
                # Actualise ne peut pas être réécrit en place pendant
                # qu'il tourne (PermissionError sous Windows sur son
                # propre .exe) : extraction dans un dossier temporaire
                # distinct, puis bascule par renommage fichier à
                # fichier — voir CONCEPTION.md, « Garde-fou
                # anti-boucle infinie ». Le manifeste est appliqué
                # après la bascule, directement sur
                # repertoire_installation : il vise des fichiers
                # obsolètes de l'installation déjà en place (pas
                # nécessairement présents dans le zip fraîchement
                # extrait), donc n'aurait aucun effet s'il était
                # appliqué sur le dossier temporaire.
                with tempfile.TemporaryDirectory(
                    dir=repertoire_installation, prefix="maj_temp_"
                ) as dossier_temp:
                    mise_a_jour.extraire_zip(chemin_zip, Path(dossier_temp))
                    try:
                        _basculer_par_renommage(Path(dossier_temp), repertoire_installation)
                    except OSError as erreur:
                        _LOGGER.error(
                            "Échec du renommage lors de la bascule d'auto-mise-à-jour "
                            "d'Actualise (%s) : bascule ignorée, zip source conservé "
                            "pour nouvelle tentative au prochain lancement.",
                            erreur,
                        )
                        continue

                mise_a_jour.appliquer_manifeste(manifest, repertoire_installation)
            else:
                # L'exécutable de l'application cible n'est pas en
                # cours d'exécution au moment de la bascule (contexte
                # différent d'Actualise lui-même) : l'extraction
                # directe reste valide et sans risque.
                mise_a_jour.extraire_zip(chemin_zip, repertoire_installation)
                mise_a_jour.appliquer_manifeste(manifest, repertoire_installation)

            bloc_config["build_installe"] = build_zip
            config.sauvegarder_config(configuration)

            chemin_zip.unlink()

            if prefixe == "actualise":
                # Une nouvelle version d'Actualise vient d'être installée :
                # on relance la version fraîchement installée comme 2ème
                # instance (marqueur --child), puis on termine ce process
                # parent immédiatement, sans lancer l'application cible ni
                # démarrer la tâche de fond — l'enfant reprend la suite de
                # la séquence de démarrage à sa place. Voir CONCEPTION.md,
                # « Garde-fou anti-boucle infinie ».
                _relancer_en_enfant()
                raise SystemExit(0)
    except KeyError:
        # Champ obligatoire manquant dans config.json : cohérent avec le
        # choix déjà acté pour charger_config (config invalide = erreur
        # bloquante, pas de repli silencieux) — la KeyError continue de
        # remonter, mais avec un log explicite pour éviter une exception
        # cryptique sans contexte.
        _LOGGER.error(
            "config.json incomplet : champ obligatoire manquant lors de "
            "l'application des mises à jour en attente."
        )
        raise


def lancer_application_cible() -> None:
    """Lance immédiatement l'application cible dans sa version
    actuellement installée, sans attendre aucune vérification réseau.

    Voir CONCEPTION.md, « Séquence de démarrage », étape 2.
    """
    configuration = config.charger_config()
    bloc_config = configuration["application_cible"]
    chemin_executable = Path(bloc_config["repertoire_installation"]) / bloc_config["executable"]

    # Popen sans wait() : cycles de vie indépendants dès le lancement
    # (voir CONCEPTION.md, « Cycle de vie du processus Actualise »).
    subprocess.Popen([str(chemin_executable)])


def _url_asset_release(depot_github: str, build: int, prefixe: str) -> str:
    """Construit l'URL de l'asset zip de Release GitHub pour ``build``.

    Voir CONCEPTION.md, « Distribution des binaires — GitHub Releases » :
    un seul asset zip par tag, le tag étant ``v<build>`` (ex. ``v48``).
    Convention retenue ici pour le nom de fichier de l'asset publié :
    ``<prefixe>-v<build>.zip`` (ex. ``actualise-v48.zip``,
    ``scrabble-v4.zip``) — à documenter/adapter si un autre nommage
    d'asset est publié côté Release.
    """
    return _GABARIT_URL_RELEASE.format(depot=depot_github, build=build, fichier=f"{prefixe}-v{build}.zip")


def tache_verification_arriere_plan() -> None:
    """Tâche de fond : vérifie et télécharge les mises à jour
    (Actualise et application cible), notifie via ntfy si une mise à
    jour est prête.

    Voir CONCEPTION.md, « Séquence de démarrage », étape 3. Toute
    exception inattendue est capturée et loguée : cette tâche tourne
    dans un thread séparé, sans supervision, et ne doit jamais faire
    planter le programme.
    """
    try:
        _LOGGER.info("Démarrage de la vérification des mises à jour en arrière-plan.")

        configuration = config.charger_config()
        zone_attente = Path(configuration["zone_attente"])
        zone_attente.mkdir(parents=True, exist_ok=True)

        cibles = [
            ("actualise", configuration["actualise"]),
            (
                _prefixe_pour(configuration["application_cible"]["nom"]),
                configuration["application_cible"],
            ),
        ]

        for prefixe, bloc_config in cibles:
            distant = version_check.verifier_version(
                bloc_config["depot_github"], bloc_config["build_installe"]
            )
            if distant is None:
                continue

            build_distant = distant["build"]
            url = _url_asset_release(bloc_config["depot_github"], build_distant, prefixe)

            chemin_telecharge = mise_a_jour.telecharger_zip(url, distant["sha256"])
            if chemin_telecharge is None:
                continue

            chemin_zone_attente = zone_attente / f"{prefixe}_{build_distant}.zip"
            shutil.move(str(chemin_telecharge), str(chemin_zone_attente))

            notifications.notifier_ntfy(
                configuration["topic_ntfy"],
                f"MAJ - Mise à jour disponible pour {prefixe} (build {build_distant}) : "
                "elle sera appliquée au prochain lancement.",
            )
    except Exception:
        _LOGGER.exception("Erreur inattendue dans la tâche de vérification en arrière-plan")


def configurer_logging() -> None:
    """Configure le logging global vers un fichier, avant tout autre
    traitement de ``main()``.

    Actualise sera packagé en ``--noconsole`` (voir CONCEPTION.md) : sans
    fenêtre console, écrire sur stdout/stderr peut échouer silencieusement
    sous Windows, d'où l'écriture vers un fichier plutôt que la console.
    Le dossier de ``config.chemin_config_portable()`` peut ne pas encore
    exister au tout premier lancement (avant même que ``config.json`` n'y
    soit écrit) : il est créé si nécessaire. ``force=True`` garantit que
    cette configuration s'applique même si le logging a déjà été
    configuré (ex. appels répétés dans les tests).
    """
    chemin_log = config.chemin_config_portable() / "actualise.log"
    chemin_log.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=chemin_log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )


def main(argv: list[str] | None = None) -> int:
    """Orchestre la séquence de démarrage non bloquante d'Actualise.

    Voir CONCEPTION.md, « Séquence de démarrage — vérification non
    bloquante » pour le déroulé complet des étapes ci-dessous.
    """
    configurer_logging()

    # Bloc englobant : sans lui, une exception non anticipée par les
    # except existants (ex. config.json absent dès le tout premier
    # lancement) remonte jusqu'à --noconsole sans jamais être loguée —
    # seule une popup Windows technique s'affiche, sans rien
    # d'exploitable conservé pour diagnostiquer à distance. On logue ici
    # la stack trace complète puis on laisse l'exception se propager
    # (code de sortie non nul inchangé) : le but est d'ajouter la trace
    # au log, pas de supprimer le crash. ``SystemExit`` (ex. le
    # ``SystemExit(0)`` volontaire du garde-fou anti-boucle) hérite de
    # ``BaseException`` et n'est donc jamais intercepté ici.
    try:
        arguments = analyser_arguments(argv)

        # Étape 4 : bascule des mises à jour déjà téléchargées et validées
        # au cycle précédent (sautée pour Actualise si --child est présent).
        # Si une bascule d'Actualise lui-même vient d'avoir lieu, cette
        # fonction termine le process (SystemExit) avant de revenir ici.
        appliquer_mises_a_jour_en_attente(est_enfant=arguments.child)

        # Étape 2 : lancement immédiat de l'application cible, sans attendre
        # le réseau.
        lancer_application_cible()

        # Étape 3 : vérification et téléchargement en arrière-plan, sans
        # bloquer l'utilisateur.
        thread_verification = threading.Thread(
            target=tache_verification_arriere_plan, daemon=True
        )
        thread_verification.start()

        # Cycle de vie d'Actualise : on attend la fin de la tâche de fond
        # (pas celle de l'application cible) avant de terminer — voir
        # CONCEPTION.md, « Cycle de vie du processus Actualise ».
        thread_verification.join()
    except Exception:
        _LOGGER.exception("Actualise s'est arrêté sur une erreur fatale non gérée.")
        raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
