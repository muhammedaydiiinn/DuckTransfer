#!/usr/bin/env python3
"""
DuckTransfer derleme scripti.
macOS, Windows ve Linux'ta çalışır, platformu otomatik algılar.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


PROJECT_NAME = "DuckTransfer"
ENTRY_POINT = "main.py"
SCRIPT_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = SCRIPT_DIR / "assets"


def get_platform_info() -> tuple[str, str]:
    """(sistem, mimari) döndürür. Örn: ('darwin', 'x86_64') veya ('win32', 'AMD64')"""
    system = sys.platform  # darwin, win32, linux
    machine = platform.machine().lower()  # x86_64, arm64, AMD64
    return system, machine


def ensure_pyinstaller():
    """PyInstaller yüklü değilse kur."""
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller kuruluyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
        print("PyInstaller kuruldu.")


def build():
    system, machine = get_platform_info()

    platform_names = {
        "darwin": "macOS",
        "win32": "Windows",
        "linux": "Linux",
    }
    platform_name = platform_names.get(system, system)
    print(f"Platform: {platform_name} ({machine})")
    print(f"Proje: {PROJECT_NAME}")
    print("-" * 40)

    os.chdir(SCRIPT_DIR)
    ensure_pyinstaller()

    # PyInstaller argümanları
    # macOS: onedir + .app (onefile+windowed deprecated)
    # Windows/Linux: onefile
    use_onefile = system != "darwin"
    use_windowed = system != "linux"

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--noconfirm",
        "--noupx",
    ]
    if use_onefile:
        args.append("--onefile")
    if use_windowed:
        args.append("--windowed")

    # assets klasörünü pakete ekle (icon.png vb.)
    if ASSETS_DIR.exists():
        sep = ";" if system == "win32" else ":"
        args.extend(["--add-data", f"{ASSETS_DIR}{sep}assets"])

    # Derlenmiş exe/app ikonu
    if system == "win32":
        ico = ASSETS_DIR / "icon.ico"
        if ico.exists():
            args.extend(["--icon", str(ico)])
    elif system == "darwin":
        icns = ASSETS_DIR / "icon.icns"
        if icns.exists():
            args.extend(["--icon", str(icns)])

    args.extend([
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "boto3",
        "--hidden-import", "paramiko",
        "--hidden-import", "connectors",
        "--hidden-import", "connectors.ftp_connector",
        "--hidden-import", "connectors.sftp_connector",
        "--hidden-import", "connectors.s3_connector",
        "--hidden-import", "config",
        "--hidden-import", "config.connections",
        "--hidden-import", "ui",
        "--hidden-import", "ui.panels",
        "--hidden-import", "ui.connection_dialog",
        "--hidden-import", "ui.progress_dialog",
        "--collect-all", "ttkbootstrap",
        ENTRY_POINT,
    ])

    print("Derleme başlıyor...")
    result = subprocess.run(args)

    if result.returncode != 0:
        print("Derleme başarısız!")
        sys.exit(1)

    # Çıktı konumu
    if system == "darwin":
        out_path = SCRIPT_DIR / "dist" / f"{PROJECT_NAME}.app"
        print(f"\n✓ Derleme tamamlandı: {out_path}")
        print("  macOS .app paketi (onedir modu)")
        print("\nÇalıştırmak için: open dist/DuckTransfer.app")
    elif system == "win32":
        out_path = SCRIPT_DIR / "dist" / f"{PROJECT_NAME}.exe"
        print(f"\n✓ Derleme tamamlandı: {out_path}")
        print("\nÇalıştırmak için: dist\\DuckTransfer.exe")
    else:
        out_path = SCRIPT_DIR / "dist" / PROJECT_NAME
        print(f"\n✓ Derleme tamamlandı: {out_path}")
        print("\nÇalıştırmak için: ./dist/DuckTransfer")


if __name__ == "__main__":
    build()
