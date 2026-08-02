"""Tests unitaires pour ``actualise.py``.

Aucune exécution réelle de sous-processus ni appel réseau : ``Popen``
et les fonctions des autres modules (``config``, ``mise_a_jour``,
``version_check``, ``notifications``) sont simulés via
``unittest.mock``. Voir CONCEPTION.md, « Séquence de démarrage —
vérification non bloquante » et « Garde-fou anti-boucle infinie ».
"""

import json
import logging
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from actualise import (
    appliquer_mises_a_jour_en_attente,
    configurer_logging,
    lancer_application_cible,
    main,
    tache_verification_arriere_plan,
)


def _creer_zip_avec_manifest(chemin_zip: Path, build: int, supprimer=None) -> None:
    manifest = {"build": build, "supprimer": supprimer or []}
    with zipfile.ZipFile(chemin_zip, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("fichier.txt", "contenu")


class TestAppliquerMisesAJourEnAttenteEnfant(unittest.TestCase):
    @patch("actualise.mise_a_jour")
    @patch("actualise.config")
    def test_est_enfant_ne_fait_rien(self, mock_config, mock_mise_a_jour):
        appliquer_mises_a_jour_en_attente(est_enfant=True)

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
            appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_called_once_with(
                chemin_zip, self.repertoire_cible
            )
            mock_mise_a_jour.appliquer_manifeste.assert_called_once_with(
                {"build": 48, "supprimer": []}, self.repertoire_cible
            )

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 48)
        self.mock_config.sauvegarder_config.assert_called_once_with(self.configuration)

    def test_zip_obsolete_supprime_sans_bascule(self):
        chemin_zip = self.zone_attente / "scrabble_40.zip"
        _creer_zip_avec_manifest(chemin_zip, build=40)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config.assert_not_called()

    def test_zip_actualise_valide_relance_enfant_et_termine(self):
        chemin_zip = self.zone_attente / "actualise_11.zip"
        _creer_zip_avec_manifest(chemin_zip, build=11)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour, patch(
            "actualise._relancer_en_enfant"
        ) as mock_relancer:
            with self.assertRaises(SystemExit):
                appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_called_once_with(
                chemin_zip, self.dossier_actualise
            )
            mock_relancer.assert_called_once()

        self.assertFalse(chemin_zip.exists())
        self.assertEqual(self.configuration["actualise"]["build_installe"], 11)

    def test_aucun_zip_ne_fait_rien(self):
        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.mock_config.sauvegarder_config.assert_not_called()

    def test_plusieurs_zips_meme_prefixe_le_plus_eleve_applique_lautre_supprime(self):
        chemin_zip_bas = self.zone_attente / "scrabble_48.zip"
        chemin_zip_haut = self.zone_attente / "scrabble_49.zip"
        _creer_zip_avec_manifest(chemin_zip_bas, build=48)
        _creer_zip_avec_manifest(chemin_zip_haut, build=49)

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False)

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
            appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertTrue(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config.assert_not_called()

    def test_zip_corrompu_zip_conserve_aucune_bascule(self):
        chemin_zip = self.zone_attente / "scrabble_48.zip"
        chemin_zip.write_text("ceci n'est pas un zip")

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.assertTrue(chemin_zip.exists())
        self.assertEqual(self.configuration["application_cible"]["build_installe"], 47)
        self.mock_config.sauvegarder_config.assert_not_called()

    def test_zone_attente_inexistante_aucune_exception(self):
        self.zone_attente.rmdir()

        with patch("actualise.mise_a_jour") as mock_mise_a_jour:
            appliquer_mises_a_jour_en_attente(est_enfant=False)

            mock_mise_a_jour.extraire_zip.assert_not_called()
            mock_mise_a_jour.appliquer_manifeste.assert_not_called()

        self.mock_config.sauvegarder_config.assert_not_called()

    def test_config_incomplete_keyerror_levee_avec_log_derreur(self):
        del self.configuration["application_cible"]

        with patch("actualise.mise_a_jour"), self.assertLogs(
            "actualise", level="ERROR"
        ) as journal:
            with self.assertRaises(KeyError):
                appliquer_mises_a_jour_en_attente(est_enfant=False)

        self.assertTrue(any("config.json" in message for message in journal.output))


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


class TestLancerApplicationCible(unittest.TestCase):
    @patch("actualise.subprocess.Popen")
    @patch("actualise.config")
    def test_popen_appele_avec_le_bon_chemin_sans_wait(self, mock_config, mock_popen):
        mock_config.charger_config.return_value = {
            "application_cible": {
                "repertoire_installation": "/opt/scrabble",
                "executable": "Scrabble.exe",
                "nom": "Scrabble",
                "build_installe": 47,
                "depot_github": "AlainDelree/Scrabble",
            }
        }
        mock_processus = MagicMock()
        mock_popen.return_value = mock_processus

        lancer_application_cible()

        mock_popen.assert_called_once_with([str(Path("/opt/scrabble") / "Scrabble.exe")])
        mock_processus.wait.assert_not_called()


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

            tache_verification_arriere_plan()

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

    def test_pas_de_mise_a_jour_ne_fait_rien(self):
        with patch("actualise.version_check") as mock_version_check, patch(
            "actualise.mise_a_jour"
        ) as mock_mise_a_jour, patch("actualise.notifications") as mock_notifications:
            mock_version_check.verifier_version.return_value = None

            tache_verification_arriere_plan()

            mock_mise_a_jour.telecharger_zip.assert_not_called()
            mock_notifications.notifier_ntfy.assert_not_called()

        self.assertFalse(self.zone_attente.exists() and any(self.zone_attente.iterdir()))

    def test_exception_inattendue_ne_se_propage_pas(self):
        with patch("actualise.config") as mock_config:
            mock_config.charger_config.side_effect = RuntimeError("boom")

            tache_verification_arriere_plan()


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
        with patch("actualise.appliquer_mises_a_jour_en_attente"), patch(
            "actualise.lancer_application_cible", side_effect=RuntimeError("boum fatal")
        ), self.assertLogs("actualise", level="ERROR") as journal:
            with self.assertRaises(RuntimeError):
                main([])

        self.assertTrue(any("erreur fatale" in message for message in journal.output))

    def test_systemexit_relance_enfant_non_intercepte_ni_logue_comme_erreur(self):
        with patch(
            "actualise.appliquer_mises_a_jour_en_attente", side_effect=SystemExit(0)
        ), patch("actualise.lancer_application_cible") as mock_lancer:
            with self.assertNoLogs("actualise", level="ERROR"):
                with self.assertRaises(SystemExit):
                    main([])

            mock_lancer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
