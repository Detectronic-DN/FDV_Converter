# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all required modules
pyside6_modules = collect_submodules('PySide6')
pandas_modules = collect_submodules('pandas')
openpyxl_modules = collect_submodules('openpyxl')
requests_modules = collect_submodules('requests')
keyring_modules = collect_submodules('keyring')
pendulum_modules = collect_submodules('pendulum')

a = Analysis(
    ['src\\UI\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
    ] +
           collect_data_files('PySide6') +
           collect_data_files('pandas') +
           collect_data_files('openpyxl') +
           collect_data_files('requests') +
           collect_data_files('keyring') +
           collect_data_files('pendulum'),
    hiddenimports=[
        'src.backend', 'src.calculator', 'src.dd', 'src.FDV',
        'src.Interiem_reports', 'src.logger', 'src.UI', 'src.worker',
        'PySide6', 'pandas', 'openpyxl', 'requests', 'keyring', 'pendulum'
    ] + pyside6_modules + pandas_modules + openpyxl_modules +
      requests_modules + keyring_modules + pendulum_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FDV Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    
)