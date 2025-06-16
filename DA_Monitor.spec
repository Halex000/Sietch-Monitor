# DA_Monitor.spec
# -*- mode: python -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hidden_imports = collect_submodules('playwright')
datas = collect_data_files('playwright')

# On Windows, playwright installs to %LOCALAPPDATA%\ms-playwright
cache_dir = os.path.expandvars(r'%LOCALAPPDATA%\ms-playwright')
for root, dirs, files in os.walk(cache_dir):
    for fn in files:
        src = os.path.join(root, fn)
        # inside the exe we’ll refer to them as 'ms-playwright/...'
        dst = os.path.join('ms-playwright', os.path.relpath(root, cache_dir))
        datas.append((src, dst))

block_cipher = None

a = Analysis(
    ['DA_Sietch_Lock_Monitor.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DA_Sietch_Lock_Monitor',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    bootloader_ignore_signals=False
)
