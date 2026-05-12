# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('andy_doll.png', '.'), ('control_panel.html', '.'), ('control_panel_full.html', '.'), ('student_portal.html', '.'), ('portal_pro.html', '.'), ('launch_chrome_guard.sh', '.'), ('anti_hover_ext', 'anti_hover_ext')],
    hiddenimports=['requests', 'psutil', 'PIL', 'PIL._tkinter_finder'],
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
    name='FocusGuardPro',
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
app = BUNDLE(
    exe,
    name='FocusGuardPro.app',
    icon=None,
    bundle_identifier=None,
)
