# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller pour l'exécutable Windows d'ActualiseUI (issue #44).

Build : ``pyinstaller actualise_ui.spec`` (depuis la racine du dépôt, avec
l'environnement virtuel du projet activé — ``pyinstaller`` installé).
Sortie en mode ``--onefile`` dans ``dist/ActualiseUI.exe`` (un seul
fichier, contrairement à ``actualise.spec`` qui produit un dossier
``dist/Actualise/``) : ActualiseUI est une petite fenêtre de choix
(tkinter) lancée ponctuellement par l'application cible, pas un service
persistant — pas besoin d'un ``_internal\\`` séparé pour ce composant.

ActualiseUI doit rester invisible en dehors de sa fenêtre tkinter :
``console=False``/``noconsole=True`` (voir ``actualise_ui.py``, docstring
de module — fenêtre de choix affichée sans console parasite).

Données embarquées (``datas``) et imports cachés (``hiddenimports``)
----------------------------------------------------------------------
Volontairement vides. ``actualise_ui.py`` n'a pas de dépendance externe
(``argparse``, ``subprocess``, ``tkinter``, ``pathlib`` — tous dans la
bibliothèque standard) ; ``tkinter`` est détecté et embarqué
automatiquement par PyInstaller sans déclaration explicite. Pas de
ressource statique chargée au runtime (confirmé en lisant
``actualise_ui.py`` en entier).
"""

a = Analysis(
    ['actualise_ui.py'],
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
    a.binaries,
    a.datas,
    [],
    name='ActualiseUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Invisible hors de sa fenêtre tkinter (issue #44).
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
