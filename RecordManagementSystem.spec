# PyInstaller spec — cross-platform bundle.
#
# Build with:
#   pyinstaller RecordManagementSystem.spec
#
# Produces dist/RecordManagementSystem/  on Windows + Linux
#      and dist/RecordManagementSystem.app on macOS

import sys

block_cipher = None
app_name = "RecordManagementSystem"

# (source_path, destination_dir_inside_bundle)
datas = [
    ("src/conf/config.json", "conf"),
    ("src/icons/favorite.png", "icons"),
]

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app — no console window
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{app_name}.app",
        icon=None,
        bundle_identifier="com.example.recordmanagementsystem",
        info_plist={
            "CFBundleName": "Record Management System",
            "CFBundleDisplayName": "Record Management System",
            "NSHighResolutionCapable": True,
        },
    )
