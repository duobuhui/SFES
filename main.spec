# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata
import platform

datas = [("langs", "langs")]

if platform.system() == "Windows":
    name = "SFES-Windows"
elif platform.system() == "Linux":
    name = "SFES-Linux"
elif platform.system() == "Darwin":
    print(platform.machine())
    if "arm" in platform.machine():
        name = "SFES-macOS-Apple_Silicon"
    elif "64" in platform.machine():
        name = "SFES-macOS-Intel"
    else:
        name = "SFES-macOS"
else:
    name = "SFES"

import os
env = os.environ.get("debug", "distribution")
version = os.environ.get("version", "unknown")
name = f"{env}-{version}-" + name

a = Analysis(
    ["boot.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "bili_ticket_gt_python",
        "api",
        "utility",
        "i18n",
        "login",
        "geetest",
        "globals",
        "utils",
    ],
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
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
