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
    analyseur.add_argument(
        "--config",
        required=True,
        type=str.lower,
        help="Nom de l'application cible gérée par cette instance (ex. scrabble, rummikub)",
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


def _relancer_en_enfant(nom_app: str) -> None:
    """Relance une 2ème instance d'Actualise avec le marqueur ``--child``.

    Voir CONCEPTION.md, « Garde-fou anti-boucle infinie ». Gère aussi
    bien le cas d'un exécutable PyInstaller gelé (``sys.frozen``) que
    l'exécution directe du script Python. ``nom_app`` ne sert plus à
    lancer une application cible (Actualise ne lance plus aucun jeu) :
    il est uniquement reconstruit en ``--config nom_app`` pour que
    l'enfant sache pour quelle application cible poursuivre la
    vérification/mise à jour en arrière-plan.
    """
    if getattr(sys, "frozen", False):
        commande = [sys.executable, "--child", "--config", nom_app]
    else:
        commande = [sys.executable, str(Path(__file__).resolve()), "--child", "--config", nom_app]

    subprocess.Popen(commande)


_NOM_EXECUTABLE = "Actualise.exe"
_NOM_DOSSIER_INTERNAL = "_internal"
_NOM_FLAG_MAJ_ACTUALISE = "actualise_update.flag"


def _basculer_par_renommage(dossier_source: Path, destination: Path) -> None:
    """Bascule le contenu de ``dossier_source`` (dossier temporaire
    d'extraction) vers ``destination``, fichier par fichier, via
    renommage (``os.replace``) plutôt qu'une réécriture en place.

    Un ``.exe`` en cours d'exécution ne peut pas être réécrit en place
    sous Windows (``PermissionError``/``WinError 5``, ``os.replace``
    devant implicitement supprimer la destination avant d'y déplacer la
    source) — voir CONCEPTION.md, « Garde-fou anti-boucle infinie ».
    Cas particulier de ``_NOM_EXECUTABLE`` (``Actualise.exe``) : Windows
    autorise en revanche de le *renommer* pendant qu'il tourne, d'où une
    bascule en deux temps propre à ce fichier — renommage de l'exécutable
    courant en ``Actualise.exe.old`` (nom alors libéré), puis déplacement
    du nouvel exécutable vers ce nom libéré (simple déplacement, plus un
    remplacement). Le reliquat ``.old`` est nettoyé au lancement suivant
    par ``_nettoyer_ancien_executable``. Toute ``OSError`` (ex. fichier
    encore verrouillé) remonte telle quelle à l'appelant, qui décide de
    la marche à suivre (conservation du zip source pour nouvelle
    tentative).

    Cas particulier de ``_NOM_DOSSIER_INTERNAL`` (``_internal``, dossier
    PyInstaller contenant les ``.pyd``/``.dll`` chargés en mémoire par le
    processus en cours) : contrairement à ``_NOM_EXECUTABLE``, ces
    fichiers ne peuvent pas être renommés individuellement (verrou par
    fichier). Windows autorise en revanche de renommer le *dossier*
    entier même si des fichiers à l'intérieur sont verrouillés — même
    bascule en deux temps que ``_NOM_EXECUTABLE``, mais appliquée au
    dossier comme un bloc, avant la boucle fichier par fichier ci-dessous
    (qui exclut alors ce dossier, déjà traité).
    """
    dossier_internal_source = dossier_source / _NOM_DOSSIER_INTERNAL
    dossier_internal_destination = destination / _NOM_DOSSIER_INTERNAL
    bascule_internal_en_bloc = (
        dossier_internal_source.is_dir() and dossier_internal_destination.is_dir()
    )
    if bascule_internal_en_bloc:
        dossier_internal_destination.replace(
            dossier_internal_destination.with_name(f"{_NOM_DOSSIER_INTERNAL}.old")
        )
        os.replace(dossier_internal_source, dossier_internal_destination)

    for chemin_source in dossier_source.rglob("*"):
        chemin_relatif = chemin_source.relative_to(dossier_source)
        if bascule_internal_en_bloc and chemin_relatif.parts[0] == _NOM_DOSSIER_INTERNAL:
            continue
        chemin_destination = destination / chemin_relatif
        if chemin_source.is_dir():
            chemin_destination.mkdir(parents=True, exist_ok=True)
        else:
            chemin_destination.parent.mkdir(parents=True, exist_ok=True)
            if chemin_destination.name == _NOM_EXECUTABLE and chemin_destination.exists():
                chemin_destination.replace(chemin_destination.with_name(f"{_NOM_EXECUTABLE}.old"))
            os.replace(chemin_source, chemin_destination)


def _nettoyer_ancien_executable() -> None:
    """Supprime silencieusement les reliquats ``Actualise.exe.old`` et
    ``_internal.old`` laissés par une bascule d'auto-mise-à-jour
    précédente, s'ils existent.

    Voir ``_basculer_par_renommage`` : le renommage préalable de
    l'exécutable courant en ``.old`` (seule opération autorisée par
    Windows sur un ``.exe`` en cours d'exécution) laisse ce fichier une
    fois la bascule terminée. Il n'est plus verrouillé par personne dès
    que ce nouveau lancement démarre : nettoyage au tout début du
    lancement suivant. Même principe pour ``_internal.old`` (dossier),
    à ceci près que ``shutil.rmtree`` peut échouer si le nettoyage
    intervient trop tôt (fichiers encore verrouillés par l'ancien
    processus en cours de terminaison) : l'erreur est alors ignorée
    silencieusement, le nettoyage sera retenté au lancement suivant.
    """
    dossier_portable = config.chemin_config_portable()

    chemin_ancien = dossier_portable / f"{_NOM_EXECUTABLE}.old"
    chemin_ancien.unlink(missing_ok=True)

    dossier_internal_ancien = dossier_portable / f"{_NOM_DOSSIER_INTERNAL}.old"
    if dossier_internal_ancien.is_dir():
        shutil.rmtree(dossier_internal_ancien, ignore_errors=True)


def appliquer_mises_a_jour_en_attente(est_enfant: bool, nom_app: str) -> None:
    """Applique, au lancement, les mises à jour mises en attente au
    cycle précédent (étape 4 de la séquence de démarrage).

    Si ``est_enfant`` est vrai (marqueur ``--child`` présent), cette
    étape est sautée inconditionnellement pour Actualise lui-même — voir
    CONCEPTION.md, « Garde-fou anti-boucle infinie ».
    """
    if est_enfant:
        return

    configuration = config.charger_config(nom_app)

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

            if prefixe == "actualise" and (
                Path(configuration["application_cible"]["repertoire_installation"])
                / _NOM_FLAG_MAJ_ACTUALISE
            ).exists():
                # Le flag est présent : ActualiseUI.exe attend encore la
                # validation de l'utilisateur (ou le bat est déjà en
                # cours d'exécution) — ne pas tenter la bascule par
                # renommage en parallèle, laisser le bat gérer seul.
                _LOGGER.info(
                    "Mise à jour Actualise en attente de validation utilisateur "
                    "(flag présent)."
                )
                continue

            if build_zip <= bloc_config["build_installe"]:
                # Résidu obsolète (déjà appliqué à un cycle précédent, ou
                # périmé) : nettoyage automatique sans bascule, voir
                # CONCEPTION.md « Nommage versionné des zips en zone
                # d'attente ».
                chemin_zip.unlink()
                continue

            try:
                with zipfile.ZipFile(chemin_zip) as archive:
                    manifest = json.loads(
                        archive.read("manifest.json").decode("utf-8-sig")
                    )
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

                bloc_config["build_installe"] = build_zip
                config.sauvegarder_config_actualise(
                    configuration["actualise"], configuration["zone_attente"]
                )
                chemin_zip.unlink()

                # Une nouvelle version d'Actualise vient d'être installée :
                # on relance la version fraîchement installée comme 2ème
                # instance (marqueur --child), puis on termine ce process
                # parent immédiatement, sans démarrer la tâche de fond —
                # l'enfant reprend la suite de la séquence de démarrage à
                # sa place. Voir CONCEPTION.md, « Garde-fou anti-boucle
                # infinie ».
                _relancer_en_enfant(nom_app)
                raise SystemExit(0)
            else:
                # Un zip de jeu ne s'applique plus que via le bat généré
                # ci-dessous, déclenché par le jeu lui-même à sa
                # fermeture (voir CONCEPTION.md, issue #73) : jamais
                # d'extraction directe ici (l'exécutable du jeu peut
                # être en cours d'exécution — c'est précisément le cas
                # normal, puisque c'est lui qui a lancé Actualise), et
                # ``build_installe``/le zip ne sont jamais touchés tant
                # que le bat n'a pas réussi dans son intégralité. Le
                # ``manifest`` lu ci-dessus n'a servi ici qu'à valider
                # que le zip est lisible et bien formé ; il n'est pas
                # appliqué par le bat (voir
                # ``_generer_updater_bat_jeu``).
                _assurer_maj_jeu_en_attente(
                    nom_app, bloc_config, repertoire_installation, chemin_zip, build_zip
                )
    except KeyError:
        # Champ obligatoire manquant dans config_actualise.json ou
        # config_<nom_app>.json : cohérent avec le choix déjà acté pour
        # charger_config (config invalide = erreur bloquante, pas de
        # repli silencieux) — la KeyError continue de remonter, mais
        # avec un log explicite pour éviter une exception cryptique sans
        # contexte.
        _LOGGER.error(
            "config_actualise.json/config_%s.json incomplet : champ obligatoire "
            "manquant lors de l'application des mises à jour en attente.",
            nom_app,
        )
        raise


_NOM_FICHIER_CONFIG_ACTUALISE = "config_actualise.json"

_GABARIT_UPDATER_BAT = """@echo off
setlocal enabledelayedexpansion
cd /d "{dossier_actualise}"

set "LOG=updater.log"
set "ZIP={chemin_zip}"
set "FLAG={chemin_flag}"
set "CONFIG={chemin_config_actualise}"
set "BUILD={build}"
set "EXTRACT_DIR=maj_bat"

rem ACTUALISE_UPDATER_MAX_ATTENTE (secondes) : surchargeable par
rem variable d'environnement pour les tests, sinon valeur par defaut.
if not defined ACTUALISE_UPDATER_MAX_ATTENTE set "ACTUALISE_UPDATER_MAX_ATTENTE=30"

rem Rotation du journal : évite une croissance illimitée sur plusieurs
rem exécutions successives, en gardant un historique raisonnable.
if exist "%LOG%" (
    for %%A in ("%LOG%") do if %%~zA GTR 102400 (
        powershell -NoProfile -Command "try {{ (Get-Content -LiteralPath '%LOG%' -Tail 200) | Set-Content -LiteralPath '%LOG%' -Encoding UTF8 }} catch {{ }}"
    )
)

call :log "=== updater.bat demarre (build cible %BUILD%) ==="

rem 1) Attend reellement la fin de Actualise.exe et ActualiseUI.exe (qui
rem    verrouillent _internal/Actualise.exe/ActualiseUI.exe pendant leur
rem    execution) avant de toucher a quoi que ce soit. Abandon sans
rem    aucune modification si la limite de temps est atteinte.
set "_ATTENTES=0"
:attente_processus
set "_ENCORE=0"
tasklist /fi "imagename eq Actualise.exe" 2>nul | findstr /i "Actualise.exe" >nul && set "_ENCORE=1"
tasklist /fi "imagename eq ActualiseUI.exe" 2>nul | findstr /i "ActualiseUI.exe" >nul && set "_ENCORE=1"
if "%_ENCORE%"=="0" goto :processus_termines
set /a _ATTENTES+=1
if %_ATTENTES% GEQ %ACTUALISE_UPDATER_MAX_ATTENTE% (
    call :log "ABANDON : Actualise.exe ou ActualiseUI.exe tourne encore apres !_ATTENTES!s d'attente, bascule annulee, rien modifie."
    goto :fin
)
timeout /t 1 /nobreak > nul
goto :attente_processus
:processus_termines

rem Nettoyage des reliquats d'une tentative precedente, avant de
rem recommencer (ne rien supposer sur leur presence).
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%"
if exist "_internal.old" rmdir /s /q "_internal.old"
if exist "Actualise.exe.old" del /f "Actualise.exe.old"
if exist "ActualiseUI.exe.old" del /f "ActualiseUI.exe.old"

rem 2) Extraction controlee : zip invalide/illisible = echec detecte,
rem    rien n'est modifie, le zip est conserve pour une nouvelle
rem    tentative au prochain declenchement.
powershell -NoProfile -Command "try {{ Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%EXTRACT_DIR%' -Force; exit 0 }} catch {{ exit 1 }}"
if errorlevel 1 (
    call :log "ECHEC : extraction du zip impossible (zip invalide ou illisible) ; rien modifie, zip conserve."
    rmdir /s /q "%EXTRACT_DIR%" 2>nul
    goto :fin
)
if not exist "%EXTRACT_DIR%\\_internal" (
    call :log "ECHEC : _internal absent de l'archive extraite ; rien modifie, zip conserve."
    rmdir /s /q "%EXTRACT_DIR%" 2>nul
    goto :fin
)
if not exist "%EXTRACT_DIR%\\Actualise.exe" (
    call :log "ECHEC : Actualise.exe absent de l'archive extraite ; rien modifie, zip conserve."
    rmdir /s /q "%EXTRACT_DIR%" 2>nul
    goto :fin
)
if not exist "%EXTRACT_DIR%\\ActualiseUI.exe" (
    call :log "ECHEC : ActualiseUI.exe absent de l'archive extraite ; rien modifie, zip conserve."
    rmdir /s /q "%EXTRACT_DIR%" 2>nul
    goto :fin
)

rem 3) Bascule des trois elements, chacune controlee (renommage puis
rem    deplacement vers le nom libere - jamais un deplacement direct
rem    vers un nom de dossier/fichier encore existant, qui imbriquerait
rem    le contenu au lieu de le remplacer). Tout echec declenche la
rem    restauration de ce qui a deja ete bascule (ordre inverse).
set "_OK_INTERNAL=0"
set "_OK_EXE=0"
set "_OK_UI=0"

ren "_internal" "_internal.old"
if errorlevel 1 (
    call :log "ECHEC : _internal verrouille, renommage impossible ; rien modifie, zip conserve."
    goto :fin
)
move /y "%EXTRACT_DIR%\\_internal" "_internal" >nul
if errorlevel 1 (
    call :log "ECHEC : impossible de deplacer le nouveau _internal ; restauration."
    ren "_internal.old" "_internal"
    goto :fin
)
set "_OK_INTERNAL=1"

ren "Actualise.exe" "Actualise.exe.old"
if errorlevel 1 (
    call :log "ECHEC : Actualise.exe verrouille, renommage impossible ; restauration."
    goto :annuler
)
move /y "%EXTRACT_DIR%\\Actualise.exe" "Actualise.exe" >nul
if errorlevel 1 (
    call :log "ECHEC : impossible de deplacer le nouveau Actualise.exe ; restauration."
    ren "Actualise.exe.old" "Actualise.exe"
    goto :annuler
)
set "_OK_EXE=1"

ren "ActualiseUI.exe" "ActualiseUI.exe.old"
if errorlevel 1 (
    call :log "ECHEC : ActualiseUI.exe verrouille, renommage impossible ; restauration."
    goto :annuler
)
move /y "%EXTRACT_DIR%\\ActualiseUI.exe" "ActualiseUI.exe" >nul
if errorlevel 1 (
    call :log "ECHEC : impossible de deplacer le nouveau ActualiseUI.exe ; restauration."
    ren "ActualiseUI.exe.old" "ActualiseUI.exe"
    goto :annuler
)
set "_OK_UI=1"

goto :bascule_ok

:annuler
if "%_OK_UI%"=="1" (
    del /f "ActualiseUI.exe" 2>nul
    ren "ActualiseUI.exe.old" "ActualiseUI.exe"
)
if "%_OK_EXE%"=="1" (
    del /f "Actualise.exe" 2>nul
    ren "Actualise.exe.old" "Actualise.exe"
)
if "%_OK_INTERNAL%"=="1" (
    rmdir /s /q "_internal" 2>nul
    ren "_internal.old" "_internal"
)
call :log "Bascule annulee, installation restauree dans son etat initial ; zip conserve."
rmdir /s /q "%EXTRACT_DIR%" 2>nul
goto :fin

:bascule_ok
call :log "Bascule reussie : _internal, Actualise.exe et ActualiseUI.exe remplaces."
rmdir /s /q "%EXTRACT_DIR%" 2>nul
if exist "_internal.old" rmdir /s /q "_internal.old"
if exist "Actualise.exe.old" del /f "Actualise.exe.old"
if exist "ActualiseUI.exe.old" del /f "ActualiseUI.exe.old"

rem 4) build_installe n'est reecrit qu'une fois la bascule des fichiers
rem    effectivement reussie - jamais avant, jamais si elle a echoue.
powershell -NoProfile -Command "try {{ $p = '%CONFIG%'; $cfg = Get-Content -Raw -Path $p | ConvertFrom-Json; $cfg.build_installe = %BUILD%; $json = $cfg | ConvertTo-Json -Depth 5; $tmp = $p + '.tmp'; [System.IO.File]::WriteAllText($tmp, $json, [System.Text.UTF8Encoding]::new($false)); Move-Item -Force $tmp $p; exit 0 }} catch {{ exit 1 }}"
if errorlevel 1 (
    call :log "ATTENTION : bascule des fichiers reussie mais echec de l'ecriture de build_installe dans config_actualise.json."
    goto :fin
)
call :log "build_installe reecrit a %BUILD%."

del /f "%ZIP%" 2>nul
del /f "%FLAG%" 2>nul
call :log "Zip et flag supprimes, mise a jour terminee avec succes."

if "%~1"=="--relancer" start "" "%~2"

:fin
endlocal
goto :eof

:log
>>"%LOG%" echo %date% %time% %~1
exit /b 0
"""


def _generer_updater_bat(
    chemin_zip: Path, dossier_actualise: Path, chemin_flag: Path, build: int
) -> Path:
    """Génère ``updater.bat`` dans ``dossier_actualise``, tous les
    chemins étant hardcodés au moment de la génération.

    Actualise ne peut pas se remplacer lui-même pendant qu'il tourne
    (verrous Windows sur ``_internal``/``Actualise.exe``, voir
    ``_basculer_par_renommage``) : ce bat, lancé par ActualiseUI.exe une
    fois Actualise fermé, effectue la bascule à sa place. Retourne le
    chemin du bat généré.

    Fiabilisé par l'issue #68 (le gabarit précédent, inchangé depuis la
    v10, échouait en silence : pas d'attente réelle de la fin des
    processus, pas de contrôle des renommages/déplacements, pas de
    journal, et ``ActualiseUI.exe`` n'était jamais basculé). Le bat
    généré ici :

    1. attend réellement la fin de ``Actualise.exe`` et
       ``ActualiseUI.exe`` (``tasklist``, scrutés toutes les secondes,
       limite ``ACTUALISE_UPDATER_MAX_ATTENTE`` secondes — 30 par
       défaut, surchargeable par variable d'environnement pour les
       tests) ; abandon sans aucune modification si la limite est
       atteinte ;
    2. contrôle chaque étape (extraction, puis renommage+déplacement de
       ``_internal``, ``Actualise.exe`` et ``ActualiseUI.exe``) ; tout
       échec restaure l'installation dans son état initial (annulation
       dans l'ordre inverse des étapes déjà effectuées) et conserve le
       zip pour une nouvelle tentative — jamais de déplacement direct
       vers un nom encore existant (``move`` imbriquerait le contenu au
       lieu de le remplacer : comportement vérifié), toujours un
       renommage préalable qui libère le nom cible ;
    3. écrit un journal ``updater.log`` dans ``dossier_actualise`` (une
       ligne horodatée par étape/échec), tronqué aux 200 dernières
       lignes dès qu'il dépasse 100 Ko pour rester borné d'une exécution
       à l'autre.

    Le bat réécrit aussi ``build_installe`` dans ``config_actualise.json``
    (``{build}``, le build réellement extrait) une fois la bascule
    effective — voir issue #66 : auparavant, ce chemin de mise à jour ne
    touchait jamais cette valeur, faisant retélécharger indéfiniment la
    même version. L'écriture se fait volontairement *après* le
    remplacement de ``Actualise.exe``/``_internal``/``ActualiseUI.exe``
    et *avant* la suppression du zip source : si le bat est interrompu
    avant l'écriture, le zip reste considéré comme en attente et la
    bascule sera retentée au prochain lancement (pas de perte) ; s'il
    est interrompu après, le zip restant serait de toute façon vu comme
    un résidu obsolète (``build`` ≤ ``build_installe``) puisque la
    bascule a déjà eu lieu. Écrit via ``[System.IO.File]::WriteAllText``
    avec un ``UTF8Encoding($false)`` explicite pour garantir l'absence
    de BOM (même convention que ``config._ecrire_json_atomique``), puis
    bascule par ``Move-Item -Force`` (équivalent de l'écriture atomique
    ``os.replace`` déjà utilisée côté Python).
    """
    chemin_bat = dossier_actualise / "updater.bat"
    chemin_bat.write_text(
        _GABARIT_UPDATER_BAT.format(
            dossier_actualise=dossier_actualise,
            chemin_zip=chemin_zip,
            chemin_flag=chemin_flag,
            chemin_config_actualise=dossier_actualise / _NOM_FICHIER_CONFIG_ACTUALISE,
            build=build,
        ),
        encoding="utf-8",
    )
    return chemin_bat


def _ecrire_flag_maj(
    repertoire_app_cible: Path, chemin_bat: Path, dossier_actualise: Path, type_maj: str
) -> None:
    """Écrit ``actualise_update.flag`` dans le dossier d'installation de
    l'application cible.

    Détecté par l'application cible à son démarrage pour lancer
    ActualiseUI.exe, qui présente à l'utilisateur le choix d'appliquer
    la mise à jour (voir CONCEPTION.md). ``type_maj`` (``"actualise"``
    ou ``"jeu"``) est un champ facultatif, purement informationnel : le
    code déjà déployé dans les jeux ne teste que l'existence du fichier
    (son nom littéral), il ne lit ni n'exige ce champ — il ne sert qu'au
    diagnostic humain (lecture du flag, journal).
    """
    chemin_flag = repertoire_app_cible / _NOM_FLAG_MAJ_ACTUALISE
    contenu = {
        "actualise_ui": str(dossier_actualise / "ActualiseUI.exe"),
        "bat": str(chemin_bat),
        "type": type_maj,
    }
    chemin_flag.write_text(json.dumps(contenu, indent=4), encoding="utf-8")


def _lister_entrees_racine_zip(chemin_zip: Path) -> list[str]:
    """Liste les entrées de premier niveau (nom avant le premier ``/``)
    d'un zip, sans doublons, dans leur ordre d'apparition dans l'archive.

    Utilisé pour générer dynamiquement les blocs de bascule du bat de
    mise à jour d'un jeu (``_generer_updater_bat_jeu``) : contrairement
    au zip d'Actualise (toujours ``_internal``/``Actualise.exe``/
    ``ActualiseUI.exe``, connus à l'avance), le contenu d'un zip de jeu
    est arbitraire — il faut l'inspecter pour savoir quoi basculer.
    Lève ``zipfile.BadZipFile`` si ``chemin_zip`` n'est pas un zip lisible
    (laissé remonter tel quel à l'appelant, voir
    ``_assurer_maj_jeu_en_attente``).
    """
    vues: set[str] = set()
    entrees: list[str] = []
    with zipfile.ZipFile(chemin_zip) as archive:
        for membre in archive.namelist():
            racine = membre.split("/", 1)[0]
            if racine and racine not in vues:
                vues.add(racine)
                entrees.append(racine)
    return entrees


def _bloc_bascule_entree_jeu(indice: int, nom_entree: str) -> str:
    """Génère le bloc batch qui bascule une entrée de premier niveau
    (fichier ou dossier) du zip extrait vers le dossier d'installation
    du jeu, via renommage puis déplacement — jamais un déplacement
    direct vers un nom encore existant (voir ``_basculer_par_renommage``
    pour la même règle côté Actualise). Toute erreur de renommage ou de
    déplacement saute à ``:annuler``, après avoir restauré l'éventuelle
    sauvegarde de cette entrée elle-même (les entrées précédentes,
    marquées ``_OK_<indice>``, sont restaurées par ``:annuler``).
    """
    return (
        f'rem --- Entree {indice} : {nom_entree} ---\n'
        f'set "_OK_{indice}=0"\n'
        f'set "_HADBACKUP_{indice}=0"\n'
        f'if exist "{nom_entree}" (\n'
        f'    ren "{nom_entree}" "{nom_entree}.maj_old"\n'
        f"    if errorlevel 1 (\n"
        f'        call :log "ECHEC : {nom_entree} verrouille, renommage impossible ; restauration."\n'
        f"        goto :annuler\n"
        f"    )\n"
        f'    set "_HADBACKUP_{indice}=1"\n'
        f")\n"
        f'move /y "%EXTRACT_DIR%\\{nom_entree}" "{nom_entree}" >nul\n'
        f"if errorlevel 1 (\n"
        f'    call :log "ECHEC : impossible de deplacer {nom_entree} ; restauration."\n'
        f'    if "!_HADBACKUP_{indice}!"=="1" ren "{nom_entree}.maj_old" "{nom_entree}"\n'
        f"    goto :annuler\n"
        f")\n"
        f'set "_OK_{indice}=1"\n'
    )


def _bloc_annulation_entree_jeu(indice: int, nom_entree: str) -> str:
    """Génère le bloc batch d'annulation (ordre inverse de la bascule)
    pour une entrée déjà entièrement basculée (``_OK_<indice>==1``) :
    supprime le nouveau contenu, restaure la sauvegarde si elle existait.
    """
    return (
        f'if "!_OK_{indice}!"=="1" (\n'
        f'    if exist "{nom_entree}\\" ( rmdir /s /q "{nom_entree}" ) else ( del /f /q "{nom_entree}" 2>nul )\n'
        f'    if "!_HADBACKUP_{indice}!"=="1" ren "{nom_entree}.maj_old" "{nom_entree}"\n'
        f")\n"
    )


def _bloc_nettoyage_backup_jeu(nom_entree: str) -> str:
    """Génère le bloc batch qui supprime le reliquat ``<nom>.maj_old``
    d'une entrée, qu'il s'agisse d'un fichier ou d'un dossier — utilisé
    à la fois en nettoyage préalable (reliquat d'une tentative
    précédente interrompue) et en nettoyage final après succès.
    """
    return (
        f'if exist "{nom_entree}.maj_old\\" ( rmdir /s /q "{nom_entree}.maj_old" ) '
        f'else if exist "{nom_entree}.maj_old" ( del /f /q "{nom_entree}.maj_old" )\n'
    )


_GABARIT_UPDATER_BAT_JEU = """@echo off
setlocal enabledelayedexpansion
cd /d "{dossier_jeu}"

set "LOG=updater.log"
set "ZIP={chemin_zip}"
set "FLAG={chemin_flag}"
set "CONFIG={chemin_config_app}"
set "BUILD={build}"
set "EXECUTABLE={executable_jeu}"
set "EXTRACT_DIR=maj_bat"

rem ACTUALISE_UPDATER_MAX_ATTENTE (secondes) : surchargeable par
rem variable d'environnement pour les tests, sinon valeur par defaut.
if not defined ACTUALISE_UPDATER_MAX_ATTENTE set "ACTUALISE_UPDATER_MAX_ATTENTE=30"

rem Rotation du journal : évite une croissance illimitée sur plusieurs
rem exécutions successives, en gardant un historique raisonnable.
if exist "%LOG%" (
    for %%A in ("%LOG%") do if %%~zA GTR 102400 (
        powershell -NoProfile -Command "try {{ (Get-Content -LiteralPath '%LOG%' -Tail 200) | Set-Content -LiteralPath '%LOG%' -Encoding UTF8 }} catch {{ }}"
    )
)

call :log "=== updater.bat (jeu) demarre (build cible %BUILD%) ==="

rem 1) Attend reellement la fin du jeu lui-meme, de Actualise.exe et de
rem    ActualiseUI.exe (qui peuvent verrouiller leurs fichiers respectifs)
rem    avant de toucher a quoi que ce soit. Abandon sans aucune
rem    modification si la limite de temps est atteinte.
set "_ATTENTES=0"
:attente_processus
set "_ENCORE=0"
tasklist /fi "imagename eq %EXECUTABLE%" 2>nul | findstr /i "%EXECUTABLE%" >nul && set "_ENCORE=1"
tasklist /fi "imagename eq Actualise.exe" 2>nul | findstr /i "Actualise.exe" >nul && set "_ENCORE=1"
tasklist /fi "imagename eq ActualiseUI.exe" 2>nul | findstr /i "ActualiseUI.exe" >nul && set "_ENCORE=1"
if "%_ENCORE%"=="0" goto :processus_termines
set /a _ATTENTES+=1
if %_ATTENTES% GEQ %ACTUALISE_UPDATER_MAX_ATTENTE% (
    call :log "ABANDON : le jeu, Actualise.exe ou ActualiseUI.exe tourne encore apres !_ATTENTES!s d'attente, bascule annulee, rien modifie."
    goto :fin
)
timeout /t 1 /nobreak > nul
goto :attente_processus
:processus_termines

rem Nettoyage des reliquats d'une tentative precedente, avant de
rem recommencer (ne rien supposer sur leur presence).
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%"
{blocs_nettoyage_initial}
rem 2) Extraction controlee : zip invalide/illisible = echec detecte,
rem    rien n'est modifie, le zip est conserve pour une nouvelle
rem    tentative au prochain declenchement.
powershell -NoProfile -Command "try {{ Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%EXTRACT_DIR%' -Force; exit 0 }} catch {{ exit 1 }}"
if errorlevel 1 (
    call :log "ECHEC : extraction du zip impossible (zip invalide ou illisible) ; rien modifie, zip conserve."
    rmdir /s /q "%EXTRACT_DIR%" 2>nul
    goto :fin
)
if not exist "%EXTRACT_DIR%\\%EXECUTABLE%" (
    call :log "ECHEC : %EXECUTABLE% absent de l'archive extraite ; rien modifie, zip conserve."
    rmdir /s /q "%EXTRACT_DIR%" 2>nul
    goto :fin
)

rem 3) Bascule de chaque entree de premier niveau du zip, chacune
rem    controlee (renommage puis deplacement vers le nom libere - jamais
rem    un deplacement direct vers un nom de dossier/fichier encore
rem    existant, qui imbriquerait le contenu au lieu de le remplacer).
rem    Tout echec declenche la restauration de ce qui a deja ete
rem    bascule (ordre inverse).
{blocs_bascule}
goto :bascule_ok

:annuler
{blocs_annulation}call :log "Bascule annulee, installation restauree dans son etat initial ; zip conserve."
rmdir /s /q "%EXTRACT_DIR%" 2>nul
goto :fin

:bascule_ok
call :log "Bascule reussie : contenu du jeu remplace."
rmdir /s /q "%EXTRACT_DIR%" 2>nul
{blocs_nettoyage_final}
rem 4) build_installe n'est reecrit qu'une fois la bascule des fichiers
rem    effectivement reussie - jamais avant, jamais si elle a echoue.
powershell -NoProfile -Command "try {{ $p = '%CONFIG%'; $cfg = Get-Content -Raw -Path $p | ConvertFrom-Json; $cfg.build_installe = %BUILD%; $json = $cfg | ConvertTo-Json -Depth 5; $tmp = $p + '.tmp'; [System.IO.File]::WriteAllText($tmp, $json, [System.Text.UTF8Encoding]::new($false)); Move-Item -Force $tmp $p; exit 0 }} catch {{ exit 1 }}"
if errorlevel 1 (
    call :log "ATTENTION : bascule des fichiers reussie mais echec de l'ecriture de build_installe dans %CONFIG%."
    goto :fin
)
call :log "build_installe reecrit a %BUILD%."

del /f "%ZIP%" 2>nul
del /f "%FLAG%" 2>nul
call :log "Zip et flag supprimes, mise a jour terminee avec succes."

if "%~1"=="--relancer" start "" "%~2"

:fin
endlocal
goto :eof

:log
>>"%LOG%" echo %date% %time% %~1
exit /b 0
"""


def _generer_updater_bat_jeu(
    chemin_zip: Path,
    dossier_jeu: Path,
    chemin_flag: Path,
    chemin_config_app: Path,
    executable_jeu: str,
    build: int,
    entrees_racine: list[str],
) -> Path:
    """Génère ``updater.bat`` dans ``dossier_jeu`` (dossier d'installation
    de l'application cible), pour appliquer la mise à jour de ce jeu une
    fois le jeu fermé.

    Généralisation, pour une application cible quelconque, du mécanisme
    ``_generer_updater_bat`` déjà en place pour Actualise lui-même (voir
    CONCEPTION.md) : mêmes garanties (attente réelle des processus,
    contrôle de chaque étape avec restauration de l'état initial, journal
    ``updater.log``, ``build_installe`` réécrit seulement après succès),
    mais généralisées à un contenu de zip arbitraire — chaque entrée de
    premier niveau de l'archive (``entrees_racine``, déterminées par
    l'appelant via ``_lister_entrees_racine_zip`` au moment de la
    génération, jamais recalculées à l'exécution du bat) reçoit son
    propre bloc de bascule renommage+déplacement, au lieu des trois noms
    fixes (``_internal``, ``Actualise.exe``, ``ActualiseUI.exe``) connus
    pour Actualise. Attend en plus la fin d'``executable_jeu`` lui-même
    (Actualise n'avait jamais besoin d'attendre le jeu, puisqu'il ne
    touche jamais à ses fichiers).

    Ne traite pas ``manifest["supprimer"]`` : contrairement à l'ancienne
    extraction directe (``mise_a_jour.extraire_zip`` +
    ``mise_a_jour.appliquer_manifeste``, retirée de
    ``appliquer_mises_a_jour_en_attente`` par cette même issue #73), ce
    bat ne supprime aucun fichier au-delà de ceux remplacés par une
    entrée de même nom présente dans le zip — limitation connue et
    documentée (voir CONCEPTION.md et le rapport de l'issue #73),
    ``manifest["supprimer"]`` n'étant pas mentionné par la tâche
    demandée et son implémentation en batch générique ajoutant un risque
    non négligeable pour un gain non démontré.
    """
    blocs_bascule = "".join(
        _bloc_bascule_entree_jeu(indice, nom) for indice, nom in enumerate(entrees_racine)
    )
    blocs_annulation = "".join(
        _bloc_annulation_entree_jeu(indice, nom)
        for indice, nom in reversed(list(enumerate(entrees_racine)))
    )
    blocs_nettoyage = "".join(_bloc_nettoyage_backup_jeu(nom) for nom in entrees_racine)

    chemin_bat = dossier_jeu / "updater.bat"
    chemin_bat.write_text(
        _GABARIT_UPDATER_BAT_JEU.format(
            dossier_jeu=dossier_jeu,
            chemin_zip=chemin_zip,
            chemin_flag=chemin_flag,
            chemin_config_app=chemin_config_app,
            build=build,
            executable_jeu=executable_jeu,
            blocs_bascule=blocs_bascule,
            blocs_annulation=blocs_annulation,
            blocs_nettoyage_initial=blocs_nettoyage,
            blocs_nettoyage_final=blocs_nettoyage,
        ),
        encoding="utf-8",
    )
    return chemin_bat


def _assurer_maj_jeu_en_attente(
    nom_app: str,
    bloc_app: dict,
    repertoire_installation: Path,
    chemin_zip: Path,
    build_zip: int,
) -> None:
    """Génère, si besoin, le bat + le flag de mise à jour pour
    l'application cible (le « jeu »), généralisation du mécanisme
    flag + updater.bat déjà en place pour Actualise lui-même (voir
    CONCEPTION.md, section dédiée à la mise à jour d'un jeu).

    Ne fait **rien** — zip conservé, aucune extraction, aucun nouveau
    flag — si ``actualise_update.flag`` existe déjà dans
    ``repertoire_installation`` : un seul type de mise à jour en attente
    à la fois dans ce dossier (celle d'Actualise, traitée plus haut dans
    la même boucle d'appel, passe donc toujours en premier ; celle du
    jeu est alors reportée à un lancement ultérieur, une fois ce flag
    consommé).

    Appelée à la fois juste après le téléchargement
    (``tache_verification_arriere_plan``, pour que le bat soit prêt avant
    une éventuelle fermeture du jeu dans la même session) et à chaque
    lancement suivant tant que le zip reste en attente
    (``appliquer_mises_a_jour_en_attente``, qui rattrape une génération
    ayant échoué précédemment — ``OSError``/``BadZipFile`` transitoire).
    """
    chemin_flag = repertoire_installation / _NOM_FLAG_MAJ_ACTUALISE
    if chemin_flag.exists():
        _LOGGER.info(
            "Mise à jour de %s (build %s) reportée : un flag de mise à jour "
            "est déjà en attente dans %s.",
            nom_app,
            build_zip,
            repertoire_installation,
        )
        return

    try:
        entrees_racine = _lister_entrees_racine_zip(chemin_zip)
        chemin_bat = _generer_updater_bat_jeu(
            chemin_zip,
            repertoire_installation,
            chemin_flag,
            config.chemin_config_portable() / f"config_{nom_app}.json",
            bloc_app["executable"],
            build_zip,
            entrees_racine,
        )
        _ecrire_flag_maj(
            repertoire_installation, chemin_bat, config.chemin_config_portable(), type_maj="jeu"
        )
    except (OSError, zipfile.BadZipFile) as erreur:
        _LOGGER.error(
            "Échec de la génération du bat/flag de mise à jour pour %s (build %s) : "
            "%s — zip conservé pour nouvelle tentative.",
            nom_app,
            build_zip,
            erreur,
        )


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


def tache_verification_arriere_plan(nom_app: str) -> None:
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

        configuration = config.charger_config(nom_app)
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

            if prefixe == "actualise":
                # Actualise ne peut pas se remplacer lui-même pendant
                # qu'il tourne : le bat + le flag sont générés dès
                # maintenant, pour que l'application cible les détecte
                # à son prochain démarrage et laisse l'utilisateur
                # choisir via ActualiseUI.exe (voir CONCEPTION.md).
                try:
                    chemin_flag = (
                        Path(configuration["application_cible"]["repertoire_installation"])
                        / _NOM_FLAG_MAJ_ACTUALISE
                    )
                    chemin_bat = _generer_updater_bat(
                        chemin_zone_attente, config.chemin_config_portable(), chemin_flag, build_distant
                    )
                    _ecrire_flag_maj(
                        Path(configuration["application_cible"]["repertoire_installation"]),
                        chemin_bat,
                        config.chemin_config_portable(),
                        type_maj="actualise",
                    )
                except OSError:
                    _LOGGER.exception(
                        "Échec de la génération du bat/flag de mise à jour Actualise."
                    )
            else:
                # Mise à jour d'un jeu : le bat + le flag sont générés
                # dès maintenant (comme pour Actualise ci-dessus), pour
                # qu'ils soient prêts avant une éventuelle fermeture du
                # jeu au cours de cette même session — voir
                # CONCEPTION.md, issue #73. Ne fait rien si un flag est
                # déjà en attente dans ce dossier (ex. mise à jour
                # d'Actualise traitée juste au-dessus dans cette même
                # itération : elle passe toujours en premier).
                _assurer_maj_jeu_en_attente(
                    nom_app,
                    bloc_config,
                    Path(bloc_config["repertoire_installation"]),
                    chemin_zone_attente,
                    build_distant,
                )

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
    exister au tout premier lancement (avant même que les fichiers de
    configuration n'y soient écrits) : il est créé si nécessaire.
    ``force=True`` garantit que
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
    _nettoyer_ancien_executable()

    # Bloc englobant : sans lui, une exception non anticipée par les
    # except existants (ex. config_actualise.json ou config_<app>.json
    # absent dès le tout premier lancement) remonte jusqu'à --noconsole
    # sans jamais être loguée —
    # seule une popup Windows technique s'affiche, sans rien
    # d'exploitable conservé pour diagnostiquer à distance. On logue ici
    # la stack trace complète puis on laisse l'exception se propager
    # (code de sortie non nul inchangé) : le but est d'ajouter la trace
    # au log, pas de supprimer le crash. ``SystemExit`` (ex. le
    # ``SystemExit(0)`` volontaire du garde-fou anti-boucle) hérite de
    # ``BaseException`` et n'est donc jamais intercepté ici.
    try:
        arguments = analyser_arguments(argv)
        nom_app = arguments.config

        # Étape 4 : bascule des mises à jour déjà téléchargées et validées
        # au cycle précédent (sautée pour Actualise si --child est présent).
        # Si une bascule d'Actualise lui-même vient d'avoir lieu, cette
        # fonction termine le process (SystemExit) avant de revenir ici.
        appliquer_mises_a_jour_en_attente(est_enfant=arguments.child, nom_app=nom_app)

        # Étape 3 : vérification et téléchargement en arrière-plan, sans
        # bloquer l'utilisateur.
        thread_verification = threading.Thread(
            target=tache_verification_arriere_plan, args=(nom_app,), daemon=True
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
