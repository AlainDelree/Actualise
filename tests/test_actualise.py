"""Tests unitaires pour ``actualise.py``.

Aucune exécution réelle de sous-processus ni appel réseau : ``Popen``
et les fonctions des autres modules (``config``, ``mise_a_jour``,
``version_check``, ``notifications``) sont simulés via
``unittest.mock``. Voir CONCEPTION.md, « Séquence de démarrage —
vérification non bloquante » et « Garde-fou anti-boucle infinie ».

Exception à cette règle : ``TestGabaritUpdaterBat`` (issue #68) exécute
réellement le ``updater.bat`` généré par ``_generer_updater_bat`` dans
un dossier temporaire — un script batch ne peut être vérifié qu'en le
lançant pour de vrai. Ces tests ne font aucun appel réseau et ne sont
actifs que sous Windows (``os.name == "nt"``).
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import call, patch

from actualise import (
    _generer_updater_bat,
    appliquer_mises_a_jour_en_attente,
    configurer_logging,
    main,
    tache_verification_arriere_plan,
)


def _creer_zip_avec_manifest(chemin_zip: Path, build: int, supprimer=None) -> None:
    manifest = {"build": build, "supprimer": supprimer or []}
    with zipfile.ZipFile(chemin_zip, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("fichier.txt", "contenu")


def _creer_zip_avec_manifest_bom_utf8(chemin_zip: Path, build: int, supprimer=None) -> None:
    # InnoSetup écrit les JSON en UTF-8 avec BOM — voir issue #46 (même
    # correctif que config.py, appliqué ici à manifest.json).
    manifest = {"build": build, "supprimer": supprimer or []}
    with zipfile.ZipFile(chemin_zip, "w") as archive:
        archive.writestr(
            "manifest.json", b"\xef\xbb\xbf" + json.dumps(manifest).encode("utf-8")
        )
        archive.writestr("fichier.txt", "contenu")


class TestAppliquerMisesAJourEnAttenteEnfant(unittest.TestCase):
    @patch("actualise.mise_a_jour")
    @patch("actualise.config")
    def test_est_enfant_ne_fait_rien(self, mock_config, mock_mise_a_jour):
        appliquer_mises_a_jour_en_attente(est_enfant=True, nom_app="scrabble")

        mock_config.charger_config.assert_not_called()
        mock_mise_a_jour.extraire_zip.assert_not_called()
        mock_mise_a_jour.appliquer_manifeste.assert_not_called()


class TestAppliquerMisesAJourEnAttente(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.racine = Path(self.dossier_temp.name)

        self.zone_attente = self.racine / "attente"
        self.zone_attente.mkdir()
        self.repertoire_cible = self.racine / "cible"
        self.repertoire_cible.mkdir()
        self.dossier_actualise = self.racine / "actualise_install"
        self.dossier_actualise.mkdir()

        self.configuration = {
            "actualise": {"build_installe": 10, "depot_github": "AlainDelree/Actualise"},
            "application_cible": {
                "nom": "Scrabble",
                "depot_github": "AlainDelree/Scrabble",
                "build_installe": 47,
                "repertoire_installation": str(self.repertoire_cible),
                "executable": "Scrabble.exe",
            },
            "zone_attente": str(self.zone_attente),
            "topic_ntfy": "actualise-scrabble",
        }

        patcher_config = patch("actualise.config")
        self.mock_config = patcher_config.start()
        self.addCleanup(patcher_config.stop)
        self.mock_config.charger_config.return_value = self.configuration
        self.mock_config.chemin_config_portable.return_value = self.dossier_actualise

    def test_zip_valide_bascule_appliquee_et_config_sauvegardee(self):
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        _creer_zip_avec_manifest(chemin_zip, build=48)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_called_once_with(
                chemin_zip, self.repertoire_cible
            )
            mock_mise_a_jour.appliquer_manifeste.assert_called_once_with(
                {"build": 48, "supprimer": []}, self.repertoire_cible
            )

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 48)
        self.mock_config.sauvegarder_config_app.assert_called_once_with(
            "scrabble", self.configuration["application_cible"]
        )
        self.mock_config.sauvegarder_config_actualise.assert_not_called()

    def test_manifest_avec_bom_utf8_est_lu_correctement(self):
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        _creer_zip_avec_manifest_bom_utf8(chemin_zip, build=48)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_called_once_with(
                chemin_zip, self.repertoire_cible
            )
            mock_mise_a_jour.appliquer_manifeste.assert_called_once_with(
                {"build": 48, "supprimer": []}, self.repertoire_cible
            )

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 48)

    def test_zip_obsolete_supprime_sans_bascule(self):
        chemin_zip = self.zone_attente / "scrabble_40.zip"
        _creer_zip_avec_manifest(chemin_zip, build=40)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config_actualise.assert_not_called()
        self.mock_config.sauvegarder_config_app.assert_not_called()

    def test_zip_actualise_valide_relance_enfant_et_termine(self):
        chemin_zip = self.zone_attente / "actualise_11.zip"
        _creer_zip_avec_manifest(chemin_zip, build=11)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour, patch(
            "actualise._relancer_en_enfant"
        ) as mock_relancer:
            with self.assertRaises(SystemExit):
                appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            # L'extraction se fait dans un dossier temporaire distinct
            # (sous repertoire_installation), jamais directement dans
            # repertoire_installation lui-même — voir
            # _basculer_par_renommage.
            mock_mise_a_jour.extraire_zip.assert_called_once()
            chemin_zip_appele, dossier_extraction = mock_mise_a_jour.extraire_zip.call_args[0]
            self.assertEqual(chemin_zip_appele, chemin_zip)
            self.assertEqual(dossier_extraction.parent, self.dossier_actualise)

            mock_mise_a_jour.appliquer_manifeste.assert_called_once_with(
                {"build": 11, "supprimer": []}, self.dossier_actualise
            )
            mock_relancer.assert_called_once_with("scrabble")

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["actualise"]["build_installe"], 11)

    def test_bascule_actualise_via_dossier_temporaire_et_renommage(self):
        # Test de bout en bout (sans mocker mise_a_jour) du mécanisme de
        # bascule sécurisée : extraction dans un dossier temporaire puis
        # renommage vers repertoire_installation, jamais d'écriture
        # directe dans le dossier de l'exécutable en cours d'exécution.
        chemin_zip = self.zone_attente / "actualise_11.zip"
        _creer_zip_avec_manifest(chemin_zip, build=11)

        with patch("actualise._relancer_en_enfant") as mock_relancer:
            with self.assertRaises(SystemExit):
                appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_relancer.assert_called_once_with("scrabble")

        fichier_bascule = self.dossier_actualise / "fichier.txt"
        self.assertTrue(fichier_bascule.exists())
        self.assertEqual(fichier_bascule.read_text(), "contenu")
        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["actualise"]["build_installe"], 11)

        residus_temp = [
            chemin
            for chemin in self.dossier_actualise.iterdir()
            if chemin.name.startswith("maj_temp_")
        ]
        self.assertEqual(residus_temp, [])

    def test_echec_renommage_bascule_actualise_zip_conserve_aucune_exception(self):
        chemin_zip = self.zone_attente / "actualise_11.zip"
        _creer_zip_avec_manifest(chemin_zip, build=11)

        with patch(
            "actualise._basculer_par_renommage",
            side_effect=PermissionError("fichier encore verrouillé"),
        ), patch("actualise._relancer_en_enfant") as mock_relancer, self.assertLogs(
            "actualise", level="ERROR"
        ) as journal:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_relancer.assert_not_called()

        self.assertTrue(chemin_zip.exists())
        self.assertEqual(self.configuration["actualise"]["build_installe"], 10)
        self.mock_config.sauvegarder_config_actualise.assert_not_called()
        self.mock_config.sauvegarder_config_app.assert_not_called()
        self.assertTrue(
            any("renommage" in message.lower() for message in journal.output)
        )

    def test_application_cible_extrait_directement_sans_dossier_temporaire(self):
        # Non-régression : contrairement à Actualise lui-même, l'exécutable
        # de l'application cible n'est pas en cours d'exécution au moment
        # de la bascule, donc l'extraction directe reste inchangée.
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        _creer_zip_avec_manifest(chemin_zip, build=48)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour, patch(
            "actualise._basculer_par_renommage"
        ) as mock_basculer:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_called_once_with(
                chemin_zip, self.repertoire_cible
            )
            mock_mise_a_jour.appliquer_manifeste.assert_called_once_with(
                {"build": 48, "supprimer": []}, self.repertoire_cible
            )
            mock_basculer.assert_not_called()

        self.assertEqual(self.configuration["application_cible"]["build_installe"], 48)

    def test_echec_extraction_application_cible_zip_conserve_aucune_exception(self):
        # Non-régression issue #66 : une erreur d'extraction pour
        # l'application cible (droits insuffisants, fichier verrouillé
        # parce que l'application tourne encore) ne doit jamais faire
        # planter Actualise ni être silencieusement ignorée — le zip est
        # conservé pour une nouvelle tentative et build_installe n'est
        # pas modifié tant que la bascule n'a pas réussi.
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        _creer_zip_avec_manifest(chemin_zip, build=48)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour, self.assertLogs(
            "actualise", level="ERROR"
        ) as journal:
            mock_mise_a_jour.extraire_zip.side_effect = PermissionError(
                "Permission denied: 'C:\\Program Files\\Scrabble\\clr_loader\\"
                "ffi\\dlls\\amd64\\ClrLoader.dll'"
            )

            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertTrue(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config_app.assert_not_called()
        self.assertTrue(
            any("extraction" in message.lower() for message in journal.output)
        )

    def test_aucun_zip_ne_fait_rien(self):
        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.mock_config.sauvegarder_config_actualise.assert_not_called()
        self.mock_config.sauvegarder_config_app.assert_not_called()

    def test_plusieurs_zips_meme_prefixe_le_plus_eleve_applique_lautre_supprime(self):
        chemin_zip_bas = self.zone_attente / "scrabble_48.zip"
        chemin_zip_haut = self.zone_attente / "scrabble_49.zip"
        _creer_zip_avec_manifest(chemin_zip_bas, build=48)
        _creer_zip_avec_manifest(chemin_zip_haut, build=49)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_called_once_with(
                chemin_zip_haut, self.repertoire_cible
            )

        self.assertFalse(chemin_zip_haut.exists())
        self.assertFalse(chemin_zip_bas.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 49)

    def test_manifest_absent_zip_conserve_aucune_bascule(self):
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        with zipfile.ZipFile(chemin_zip, "w") as archive:
            archive.writestr("fichier.txt", "contenu")

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertTrue(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config_actualise.assert_not_called()
        self.mock_config.sauvegarder_config_app.assert_not_called()

    def test_zip_corrompu_zip_conserve_aucune_bascule(self):
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        chemin_zip.write_text("ceci n'est pas un zip")

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertTrue(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config_actualise.assert_not_called()
        self.mock_config.sauvegarder_config_app.assert_not_called()

    def test_zone_attente_inexistante_aucune_exception(self):
        self.zone_attente.rmdir()

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.mock_config.sauvegarder_config_actualise.assert_not_called()
        self.mock_config.sauvegarder_config_app.assert_not_called()

    def test_config_incomplete_keyerror_levee_avec_log_derreur(self):
        del self.configuration["application_cible"]

        with patch("actualise.mise_a_jour"), self.assertLogs(
            "actualise", level="ERROR"
        ) as journal:
            with self.assertRaises(KeyError):
                appliquer_mises_a_jour_en_attente(est_enfant=False, nom_app="scrabble")

        self.assertTrue(any("config_actualise.json" in message for message in journal.output))


class TestConfigurerLogging(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)

        racine_logging = logging.getLogger()
        handlers_originaux = racine_logging.handlers[:]
        niveau_original = racine_logging.level

        def restaurer():
            for handler in racine_logging.handlers[:]:
                racine_logging.removeHandler(handler)
                handler.close()
            for handler in handlers_originaux:
                racine_logging.addHandler(handler)
            racine_logging.setLevel(niveau_original)

        self.addCleanup(restaurer)

    @patch("actualise.config")
    def test_configure_un_fichier_dans_chemin_config_portable(self, mock_config):
        dossier_config = Path(self.dossier_temp.name) / "config_actualise_absent"
        mock_config.chemin_config_portable.return_value = dossier_config

        configurer_logging()

        racine_logging = logging.getLogger()
        fichiers_journal = [
            Path(handler.baseFilename)
            for handler in racine_logging.handlers
            if isinstance(handler, logging.FileHandler)
        ]

        self.assertEqual(len(fichiers_journal), 1)
        self.assertEqual(fichiers_journal[0], dossier_config / "actualise.log")
        self.assertTrue(dossier_config.is_dir())


class TestTacheVerificationArrierePlan(unittest.TestCase):
    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.zone_attente = Path(self.dossier_temp.name) / "attente"

        self.configuration = {
            "actualise": {"build_installe": 10, "depot_github": "AlainDelree/Actualise"},
            "application_cible": {
                "nom": "Scrabble",
                "depot_github": "AlainDelree/Scrabble",
                "build_installe": 47,
                "repertoire_installation": "/opt/scrabble",
                "executable": "Scrabble.exe",
            },
            "zone_attente": str(self.zone_attente),
            "topic_ntfy": "actualise-scrabble",
        }

        patcher_config = patch("actualise.config")
        self.mock_config = patcher_config.start()
        self.addCleanup(patcher_config.stop)
        self.mock_config.charger_config.return_value = self.configuration

    def test_mise_a_jour_disponible_zip_renomme_et_notification_envoyee(self):
        chemin_temp_actualise = Path(self.dossier_temp.name) / "telecharge_actualise_tmp.zip"
        chemin_temp_actualise.write_bytes(b"contenu-actualise")
        chemin_temp_scrabble = Path(self.dossier_temp.name) / "telecharge_scrabble_tmp.zip"
        chemin_temp_scrabble.write_bytes(b"contenu-scrabble")

        with patch("actualise.version_check") as mock_version_check, patch(
            "actualise.mise_a_jour"
        ) as mock_mise_a_jour, patch("actualise.notifications") as mock_notifications:
            mock_version_check.verifier_version.side_effect = [
                {"build": 11, "sha256": "hash-actualise"},
                {"build": 48, "sha256": "hash-scrabble"},
            ]
            mock_mise_a_jour.telecharger_zip.side_effect = [
                chemin_temp_actualise,
                chemin_temp_scrabble,
            ]

            tache_verification_arriere_plan("scrabble")

            self.assertEqual(mock_mise_a_jour.telecharger_zip.call_count, 2)
            mock_notifications.notifier_ntfy.assert_has_calls(
                [
                    call("actualise-scrabble", unittest.mock.ANY),
                    call("actualise-scrabble", unittest.mock.ANY),
                ]
            )
            for appel in mock_notifications.notifier_ntfy.call_args_list:
                message = appel.args[1]
                self.assertTrue(
                    message.startswith("MAJ - "),
                    f"le message ntfy devrait être préfixé par 'MAJ - ' : {message!r}",
                )

        self.assertTrue((self.zone_attente / "actualise_11.zip").exists())
        self.assertTrue((self.zone_attente / "scrabble_48.zip").exists())

    def test_bat_updater_genere_avec_le_build_reellement_telecharge(self):
        # Non-régression issue #66 : le bat généré pour la mise à jour
        # d'Actualise via la fenêtre/updater.bat doit recevoir le numéro
        # de build réellement téléchargé, pour pouvoir réécrire
        # build_installe une fois la bascule effective (sans quoi
        # config_actualise.json reste périmé et Actualise retélécharge
        # indéfiniment la même version).
        chemin_temp_actualise = Path(self.dossier_temp.name) / "telecharge_actualise_tmp.zip"
        chemin_temp_actualise.write_bytes(b"contenu-actualise")
        chemin_temp_scrabble = Path(self.dossier_temp.name) / "telecharge_scrabble_tmp.zip"
        chemin_temp_scrabble.write_bytes(b"contenu-scrabble")

        with patch("actualise.version_check") as mock_version_check, patch(
            "actualise.mise_a_jour"
        ) as mock_mise_a_jour, patch("actualise.notifications"), patch(
            "actualise._generer_updater_bat"
        ) as mock_generer_bat, patch("actualise._ecrire_flag_maj") as mock_ecrire_flag:
            mock_version_check.verifier_version.side_effect = [
                {"build": 11, "sha256": "hash-actualise"},
                {"build": 48, "sha256": "hash-scrabble"},
            ]
            mock_mise_a_jour.telecharger_zip.side_effect = [
                chemin_temp_actualise,
                chemin_temp_scrabble,
            ]

            tache_verification_arriere_plan("scrabble")

            mock_generer_bat.assert_called_once()
            build_passe = mock_generer_bat.call_args[0][-1]
            self.assertEqual(build_passe, 11)
            mock_ecrire_flag.assert_called_once()

    def test_pas_de_mise_a_jour_ne_fait_rien(self):
        with patch("actualise.version_check") as mock_version_check, patch(
            "actualise.mise_a_jour"
        ) as mock_mise_a_jour, patch("actualise.notifications") as mock_notifications:
            mock_version_check.verifier_version.return_value = None

            tache_verification_arriere_plan("scrabble")

            mock_mise_a_jour.telecharger_zip.assert_not_called()
            mock_notifications.notifier_ntfy.assert_not_called()

        self.assertFalse(self.zone_attente.exists() and any(self.zone_attente.iterdir()))

    def test_exception_inattendue_ne_se_propage_pas(self):
        with patch("actualise.config") as mock_config:
            mock_config.charger_config.side_effect = RuntimeError("boom")

            tache_verification_arriere_plan("scrabble")


class TestMain(unittest.TestCase):
    """Voir CONCEPTION.md : ``main()`` doit loguer toute exception fatale
    non anticipée par les except existants avant de la laisser se
    propager (sinon ``actualise.log`` reste vide en ``--noconsole``),
    sans jamais intercepter le ``SystemExit(0)`` volontaire du garde-fou
    anti-boucle.
    """

    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)

        patcher_config = patch("actualise.config")
        self.mock_config = patcher_config.start()
        self.addCleanup(patcher_config.stop)
        self.mock_config.chemin_config_portable.return_value = Path(self.dossier_temp.name)

    def test_exception_fatale_dans_main_loguee_et_propagee(self):
        with patch(
            "actualise.appliquer_mises_a_jour_en_attente", side_effect=RuntimeError("boum fatal")
        ), self.assertLogs("actualise", level="ERROR") as journal:
            with self.assertRaises(RuntimeError):
                main(["--config", "scrabble"])

        self.assertTrue(any("erreur fatale" in message for message in journal.output))

    def test_systemexit_relance_enfant_non_intercepte_ni_logue_comme_erreur(self):
        with patch("actualise.appliquer_mises_a_jour_en_attente", side_effect=SystemExit(0)):
            with self.assertNoLogs("actualise", level="ERROR"):
                with self.assertRaises(SystemExit):
                    main(["--config", "scrabble"])


def _creer_installation_actualise(dossier: Path) -> None:
    """Pose une fausse installation d'Actualise (3 éléments bascules
    par le bat + config_actualise.json) dans ``dossier``, tous marqués
    « ancien » pour pouvoir distinguer un remplacement réussi."""
    (dossier / "Actualise.exe").write_text("ancien-actualise-exe", encoding="utf-8")
    (dossier / "ActualiseUI.exe").write_text("ancien-actualise-ui-exe", encoding="utf-8")
    dossier_internal = dossier / "_internal"
    dossier_internal.mkdir()
    (dossier_internal / "lib.dll").write_text("ancien", encoding="utf-8")
    (dossier / "config_actualise.json").write_text(
        json.dumps({"build_installe": 10}), encoding="utf-8"
    )


def _creer_zip_mise_a_jour(chemin_zip: Path) -> None:
    """Archive de mise à jour valide, plate, avec les 3 éléments bascules
    par le bat marqués « nouveau »."""
    with zipfile.ZipFile(chemin_zip, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"supprimer": []}))
        archive.writestr("_internal/lib.dll", "nouveau")
        archive.writestr("Actualise.exe", "nouveau-actualise-exe")
        archive.writestr("ActualiseUI.exe", "nouveau-actualise-ui-exe")


@unittest.skipUnless(os.name == "nt", "updater.bat est un script Windows (cmd.exe)")
class TestGabaritUpdaterBat(unittest.TestCase):
    """Exécute réellement ``updater.bat`` (voir issue #68) dans un
    dossier temporaire : succès, fichier verrouillé, zip invalide,
    attente puis abandon si Actualise.exe tourne encore.
    """

    def setUp(self):
        self.dossier_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier_temp.cleanup)
        self.dossier_actualise = Path(self.dossier_temp.name) / "actualise_install"
        self.dossier_actualise.mkdir()
        _creer_installation_actualise(self.dossier_actualise)

        self.chemin_zip = self.dossier_actualise / "actualise_11.zip"
        self.chemin_flag = self.dossier_actualise / "actualise_update.flag"
        self.chemin_flag.write_text("{}", encoding="utf-8")
        self.chemin_config = self.dossier_actualise / "config_actualise.json"

    def _executer_bat(self, build=11, max_attente=3, timeout=60):
        chemin_bat = _generer_updater_bat(
            self.chemin_zip, self.dossier_actualise, self.chemin_flag, build
        )
        env = dict(os.environ)
        env["ACTUALISE_UPDATER_MAX_ATTENTE"] = str(max_attente)
        subprocess.run(
            ["cmd", "/c", str(chemin_bat)],
            cwd=self.dossier_actualise,
            env=env,
            timeout=timeout,
            capture_output=True,
        )

    def _journal(self) -> str:
        chemin_log = self.dossier_actualise / "updater.log"
        return chemin_log.read_text(encoding="utf-8") if chemin_log.exists() else ""

    def _assert_installation_inchangee(self):
        self.assertEqual(
            (self.dossier_actualise / "Actualise.exe").read_text(encoding="utf-8"),
            "ancien-actualise-exe",
        )
        self.assertEqual(
            (self.dossier_actualise / "ActualiseUI.exe").read_text(encoding="utf-8"),
            "ancien-actualise-ui-exe",
        )
        self.assertEqual(
            (self.dossier_actualise / "_internal" / "lib.dll").read_text(encoding="utf-8"),
            "ancien",
        )
        self.assertEqual(
            json.loads(self.chemin_config.read_text(encoding="utf-8"))["build_installe"], 10
        )
        self.assertFalse((self.dossier_actualise / "_internal.old").exists())
        self.assertFalse((self.dossier_actualise / "Actualise.exe.old").exists())
        self.assertFalse((self.dossier_actualise / "ActualiseUI.exe.old").exists())

    def test_succes_remplace_les_trois_elements_et_finalise(self):
        _creer_zip_mise_a_jour(self.chemin_zip)

        self._executer_bat(build=11)

        self.assertEqual(
            (self.dossier_actualise / "Actualise.exe").read_text(encoding="utf-8"),
            "nouveau-actualise-exe",
        )
        self.assertEqual(
            (self.dossier_actualise / "ActualiseUI.exe").read_text(encoding="utf-8"),
            "nouveau-actualise-ui-exe",
        )
        self.assertEqual(
            (self.dossier_actualise / "_internal" / "lib.dll").read_text(encoding="utf-8"),
            "nouveau",
        )
        self.assertEqual(
            json.loads(self.chemin_config.read_text(encoding="utf-8"))["build_installe"], 11
        )
        self.assertFalse(self.chemin_zip.exists())
        self.assertFalse(self.chemin_flag.exists())
        self.assertFalse((self.dossier_actualise / "_internal.old").exists())
        self.assertFalse((self.dossier_actualise / "Actualise.exe.old").exists())
        self.assertFalse((self.dossier_actualise / "ActualiseUI.exe.old").exists())
        journal = self._journal()
        self.assertIn("Bascule reussie", journal)
        self.assertIn("build_installe reecrit", journal)
        self.assertIn("succes", journal)

    def test_zip_invalide_ne_modifie_rien(self):
        self.chemin_zip.write_bytes(b"ceci n'est pas un zip valide")

        self._executer_bat(build=11)

        self._assert_installation_inchangee()
        self.assertTrue(self.chemin_zip.exists())
        self.assertTrue(self.chemin_flag.exists())
        self.assertIn("ECHEC", self._journal())
        self.assertIn("extraction", self._journal())

    def test_fichier_verrouille_restaure_l_etat_initial(self):
        # _internal est bascule avant Actualise.exe (ordre du gabarit) :
        # verrouiller Actualise.exe exerce donc le rollback d'un element
        # deja bascule (_internal), pas seulement une annulation a vide.
        _creer_zip_mise_a_jour(self.chemin_zip)
        chemin_exe = self.dossier_actualise / "Actualise.exe"

        processus_verrou = subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"$fs = [System.IO.File]::Open('{chemin_exe}', 'Open', 'ReadWrite', 'None'); "
                "Start-Sleep -Seconds 8; $fs.Close()",
            ]
        )
        try:
            time.sleep(1)
            self._executer_bat(build=11)
        finally:
            processus_verrou.wait(timeout=15)

        self._assert_installation_inchangee()
        self.assertTrue(self.chemin_zip.exists())
        self.assertTrue(self.chemin_flag.exists())
        journal = self._journal()
        self.assertIn("verrouille", journal)
        self.assertIn("restauree dans son etat initial", journal)

    def test_abandon_si_actualise_exe_tourne_encore(self):
        _creer_zip_mise_a_jour(self.chemin_zip)

        dossier_faux_process = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, dossier_faux_process, True)
        chemin_faux_exe = dossier_faux_process / "Actualise.exe"
        shutil.copy(r"C:\Windows\System32\ping.exe", chemin_faux_exe)

        processus = subprocess.Popen(
            [str(chemin_faux_exe), "-n", "8", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(1)
            self._executer_bat(build=11, max_attente=2)
        finally:
            processus.wait(timeout=15)

        self._assert_installation_inchangee()
        self.assertTrue(self.chemin_zip.exists())
        self.assertTrue(self.chemin_flag.exists())
        self.assertFalse((self.dossier_actualise / "maj_bat").exists())
        self.assertIn("ABANDON", self._journal())

    def test_attend_la_fin_du_processus_puis_termine_avec_succes(self):
        _creer_zip_mise_a_jour(self.chemin_zip)

        dossier_faux_process = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, dossier_faux_process, True)
        chemin_faux_exe = dossier_faux_process / "ActualiseUI.exe"
        shutil.copy(r"C:\Windows\System32\ping.exe", chemin_faux_exe)

        processus = subprocess.Popen(
            [str(chemin_faux_exe), "-n", "3", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            self._executer_bat(build=11, max_attente=15)
        finally:
            processus.wait(timeout=15)

        self.assertEqual(
            json.loads(self.chemin_config.read_text(encoding="utf-8"))["build_installe"], 11
        )
        self.assertFalse(self.chemin_zip.exists())
        journal = self._journal()
        self.assertIn("Bascule reussie", journal)
        self.assertNotIn("ABANDON", journal)


if __name__ == "__main__":
    unittest.main()
