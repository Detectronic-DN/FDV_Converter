# -*- mode: python ; coding: utf-8 -*-
import os

# Get the absolute path of the current working directory
project_dir = os.getcwd()

# Add the src directory to the system path
src_path = os.path.join(project_dir, 'src')


a = Analysis(
    ['src\\UI\\main.py'],
    pathex=['./'],
    binaries=[],
    datas=[
        ('version.txt', '.'),
        (os.path.join(src_path, 'UI', '*'), 'UI'),
        (os.path.join(src_path, 'backend', '*'), 'backend'),
        (os.path.join(src_path, 'calculator', '*'), 'calculator'),
        (os.path.join(src_path, 'dd', '*'), 'dd'),
        (os.path.join(src_path, 'FDV', '*'), 'FDV'),
        (os.path.join(src_path, 'Interiem_reports', '*'), 'Interiem_reports'),
        (os.path.join(src_path, 'logger', '*'), 'logger'),
        (os.path.join(src_path, 'worker', '*'), 'worker'),],
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
    name='FDV_Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
