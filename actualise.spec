# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller pour l'exécutable Windows d'Actualise (issue #328).

Build : ``pyinstaller actualise.spec`` (depuis la racine du dépôt, avec
l'environnement virtuel du projet activé — ``requests`` et ``pyinstaller``
installés). Sortie en mode ``--onedir`` dans ``dist/Actualise/``.

Actualise doit rester invisible pendant que l'application cible tourne
(voir CONCEPTION.md) : build en ``console=False`` (``--noconsole``), comme
Scrabble/Rummikub. Le mécanisme de logging vers fichier
(``actualise.configurer_logging``) existe précisément pour compenser
l'absence de console — c'est la seule trace disponible en cas de problème.

Note de cohérence (issue #328, corrigée en issue #329) : un premier commit
local avait empaqueté en ``console=True`` en argumentant qu'Actualise est un
updater CLI (``argparse``, flag ``--child``) sans besoin d'interface
graphique. Cette valeur était incohérente avec CONCEPTION.md et a été
corrigée ici avant tout push vers origin.

Données embarquées (``datas``)
-------------------------------
Volontairement vide. ``config.py.chemin_config_portable()`` résout
``config.json`` vers ``%SYSTEMDRIVE%\\Actualise\\`` (Windows) ou
``~/.config/actualise/`` (Linux) — un chemin EXTERNE à l'installation,
fourni/maintenu à côté du dossier ``dist\\Actualise\\``, jamais lu depuis
l'intérieur du paquet. Confirmé en lisant ``actualise.py``/``config.py`` en
entier : aucun autre fichier de données interne (gabarit, ressource statique,
cache) n'est chargé au runtime. Pas de ``collect_tree`` ici, à la différence
de ``scrabble.spec`` — voir ce fichier pour le rappel de l'incident dump
wiktionnaire 8,2 Go (issue #339) qui justifie de ne jamais embarquer un
dossier en bloc sans liste explicite.

Imports cachés (``hiddenimports``)
------------------------------------
Volontairement vide également. Dépendance unique du projet (voir
``requirements.txt``) : ``requests``, dont PyInstaller détecte normalement
seul les dépendances transitives (``urllib3``, ``certifi``,
``charset_normalizer``, ``idna``). Confirmé au précédent build manuel de
validation : ``dist/Actualise/_internal/`` contient déjà ``certifi/`` et
``charset_normalizer/`` sans déclaration explicite. À revérifier au premier
lancement de ``build/rebuild_actualise.bat`` (voir son étape de vérification
finale) ; si un import réseau venait à manquer à l'usage, l'ajouter ici
explicitement plutôt que de basculer sur un ``collect_all("requests")``.
"""

a = Analysis(
    ['actualise.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Actualise',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Invisible pendant que l'app cible tourne ; logging fichier compense (CONCEPTION.md).
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Actualise',
)
