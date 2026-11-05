"""Configuration pytest spécifique aux tests (ignorée par ``unittest``).

Pose le marqueur ``lent`` (déclaré dans ``pytest.ini``) sur les classes
qui exécutent réellement ``updater.bat`` sous Windows, sans ajouter de
dépendance à ``pytest`` dans ``tests/test_actualise.py`` : ce module
doit rester importable par ``python3 -m unittest discover -s tests``
même en l'absence de ``pytest``.
"""

import pytest

CLASSES_LENTES = {"TestGabaritUpdaterBat", "TestGabaritUpdaterBatJeu"}


def pytest_collection_modifyitems(items):
    for item in items:
        classe = getattr(item, "cls", None)
        if classe is not None and classe.__name__ in CLASSES_LENTES:
            item.add_marker(pytest.mark.lent)
