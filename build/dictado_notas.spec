# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller. Se ejecuta EN WINDOWS con:
#   pyinstaller build/dictado_notas.spec
#
# Empaqueta el .exe e incluye la carpeta del modelo Vosk dentro del
# propio ejecutable (--add-data), para que el instalador final sea
# "un solo click" sin que el usuario tenga que descargar nada aparte.

import os

block_cipher = None
raiz = os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))

a = Analysis(
    [os.path.join(raiz, "src", "ui.py")],
    pathex=[os.path.join(raiz, "src")],
    binaries=[],
    datas=[
        (os.path.join(raiz, "modelo_vosk_es"), "modelo_vosk_es"),
    ],
    hiddenimports=["vosk", "sounddevice", "pyttsx3.drivers", "pyttsx3.drivers.sapi5"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DictadoDeNotas",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=None,
)
