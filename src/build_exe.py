# -*- coding: utf-8 -*-
"""
Build-Skript für PyInstaller zum Erstellen der EXE.

Verwendung:
    cd src
    python build_exe.py

Das Skript erstellt eine standalone EXE in dist/
"""

import base64
from datetime import datetime
import json
import re
import sys
from pathlib import Path
import zipfile
import PyInstaller.__main__  # type: ignore


PROJECT_NAME = "Lohnsteuertabellen-Ersteller"
INITIAL_VERSION = (1, 0, 0)
VERSION_STATE_FILE_NAME = "version_state.json"


def format_version_text(version_tuple: tuple[int, int, int]) -> str:
    """Formatiere eine semantische Version im Schema major.minor.build."""
    major, minor, build = version_tuple
    return f"{major}.{minor}.{build}"


def increment_version(version_tuple: tuple[int, int, int]) -> tuple[int, int, int]:
    """Erhöhe build, rolle nach 10 Builds auf minor und nach 10 Minors auf major."""
    major, minor, build = version_tuple
    build += 1
    if build >= 10:
        build = 0
        minor += 1
    if minor >= 10:
        minor = 0
        major += 1
    return major, minor, build


def load_version_state(state_file: Path) -> tuple[int, int, int]:
    """Lade den zuletzt erfolgreich gebauten Versionsstand."""
    if not state_file.exists():
        return INITIAL_VERSION

    data = json.loads(state_file.read_text(encoding="utf-8"))
    version_tuple = (data["major"], data["minor"], data["build"])

    if any((not isinstance(value, int)) or value < 0 for value in version_tuple):
        raise ValueError(f"Ungültiger Versionsstand in {state_file}: {version_tuple}")

    return version_tuple


def determine_build_version(state_file: Path) -> tuple[int, int, int]:
    """Bestimme die Version für den aktuellen Build."""
    if not state_file.exists():
        return INITIAL_VERSION
    return increment_version(load_version_state(state_file))


def save_version_state(
    state_file: Path,
    version_tuple: tuple[int, int, int],
    build_stamp: str,
) -> None:
    """Speichere den zuletzt erfolgreich gebauten Versionsstand persistent."""
    major, minor, build = version_tuple
    state = {
        "major": major,
        "minor": minor,
        "build": build,
        "version": format_version_text(version_tuple),
        "updated_at": build_stamp,
    }
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def update_markdown_version(file_path: Path, version_text: str, stand_text: str) -> None:
    """Aktualisiere Version/Stand in Markdown-Dokumenten."""
    content = file_path.read_text(encoding="utf-8")
    content = re.sub(r"\*\*Version:\*\*.*", f"**Version:** {version_text}  ", content)
    content = re.sub(r"\*\*Stand:\*\*.*", f"**Stand:** {stand_text}  ", content)
    file_path.write_text(content, encoding="utf-8")


def regenerate_embedded_docs(readme_file: Path, tech_doc_file: Path, embedded_docs_file: Path) -> None:
    """Generiere embedded_docs.py aus docs/Liesmich.txt und docs/Dokumentation-Technik.md."""
    readme_b64 = base64.b64encode(readme_file.read_bytes()).decode("ascii")
    tech_b64 = base64.b64encode(tech_doc_file.read_bytes()).decode("ascii")

    content = f'''# -*- coding: utf-8 -*-
r"""
Eingebettete Dokumentationen (Base64-kodiert für EXE-Distribution).
Erzeugt aus docs/ Verzeichnis.
"""

import base64
from pathlib import Path
import tempfile

# Liesmich.txt (Anwender-Dokumentation) - jetzt aus docs/
README_B64 = "{readme_b64}"

# Dokumentation-Technik.md (Entwickler-Dokumentation)
TECH_DOC_B64 = "{tech_b64}"


def get_embedded_doc(which: str) -> str:
    """Dekodiere eingebettete Dokumentation.

    Args:
        which: 'readme' oder 'tech'

    Returns:
        Dekodierter Text
    """
    if which.lower() == 'readme':
        return base64.b64decode(README_B64).decode('utf-8')
    elif which.lower() == 'tech':
        return base64.b64decode(TECH_DOC_B64).decode('utf-8')
    else:
        raise ValueError(f"Unbekannte Dokumentation: {{which}}")


def get_temp_doc_path(which: str) -> Path:
    """Schreibe Dokumentation in temporäre Datei und gebe Pfad zurück.

    Args:
        which: 'readme' oder 'tech'

    Returns:
        Path zum temp file
    """
    content = get_embedded_doc(which)

    # Nutze ein persistentes Temp-Verzeichnis
    temp_dir = Path(tempfile.gettempdir()) / "lohnsteuertabellen_docs"
    temp_dir.mkdir(exist_ok=True)

    if which.lower() == 'readme':
        temp_file = temp_dir / "Liesmich.txt"
    else:
        temp_file = temp_dir / "Dokumentation-Technik.md"

    temp_file.write_text(content, encoding='utf-8')
    return temp_file
'''

    embedded_docs_file.write_text(content, encoding="utf-8")


def write_windows_version_file(
    version_file: Path,
    version_tuple: tuple[int, int, int],
    version_text: str,
    build_stamp: str,
) -> None:
    """Erzeuge Version-Resource-Datei für PyInstaller (--version-file).

    Windows-Dateiversionen benötigen vier Integer. Für das gewünschte
    Schema major.minor.build wird die vierte Komponente fest auf 0 gesetzt.
    """
    major, minor, build = version_tuple
    revision = 0
    content = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {build}, {revision}),
    prodvers=({major}, {minor}, {build}, {revision}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'GoroTech'),
        StringStruct('FileDescription', '{PROJECT_NAME}'),
        StringStruct('FileVersion', '{version_text}'),
        StringStruct('InternalName', '{PROJECT_NAME}'),
        StringStruct('LegalCopyright', 'Frei'),
        StringStruct('OriginalFilename', '{PROJECT_NAME}.exe'),
        StringStruct('ProductName', '{PROJECT_NAME}'),
        StringStruct('ProductVersion', '{version_text}'),
        StringStruct('Comments', 'Build {build_stamp}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''
    version_file.write_text(content, encoding="utf-8")


def write_runtime_version_module(version_module_file: Path, version_text: str, build_stamp: str) -> None:
    """Erzeuge Modul mit Build-Version für Laufzeitanzeige (z. B. Fenstertitel)."""
    content = f'''# -*- coding: utf-8 -*-
"""Automatisch erzeugt durch build_exe.py - nicht manuell bearbeiten."""

APP_VERSION = "{version_text}"
BUILD_STAMP = "{build_stamp}"
'''
    version_module_file.write_text(content, encoding="utf-8")


def create_release_zip(
    root_dir: Path,
    docs_dir: Path,
    exe_file: Path,
    version_text: str,
) -> Path:
    """Erstelle ein ZIP-Release mit EXE + docs/ im Projektbasisverzeichnis."""
    release_dir = root_dir / "release"
    release_dir.mkdir(parents=True, exist_ok=True)

    zip_file = release_dir / f"Lohnsteuertabellen-Ersteller_{version_text}.zip"

    with zipfile.ZipFile(zip_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_file, arcname=exe_file.name)

        for doc_file in docs_dir.rglob("*"):
            if doc_file.is_file():
                arcname = Path("docs") / doc_file.relative_to(docs_dir)
                zf.write(doc_file, arcname=str(arcname))

    return zip_file


def build_exe():
    """Baut EXE mit PyInstaller."""

    now = datetime.now()
    stand_text = now.strftime("%d.%m.%Y")
    build_stamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # Pfade
    src_dir = Path(__file__).resolve().parent
    root_dir = src_dir.parent
    version_state_file = root_dir / VERSION_STATE_FILE_NAME
    docs_dir = root_dir / "docs"
    gui_file = src_dir / "tax_table_gui.py"
    embedded_docs_file = src_dir / "embedded_docs.py"
    icon_file = src_dir / "app_icon.ico"
    docs_readme_file = docs_dir / "Liesmich.txt"
    docs_tech_file = docs_dir / "Dokumentation-Technik.md"
    pap_xml_dir = root_dir / "data" / "pap_xml"
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    version_file = build_dir / "version_info.txt"
    runtime_version_file = src_dir / "build_version.py"
    version_tuple = determine_build_version(version_state_file)
    major, minor, build = version_tuple
    version_text = format_version_text(version_tuple)
    
    # Validierungen
    if not gui_file.exists():
        print(f"❌ Fehler: {gui_file} nicht gefunden!")
        return 1

    if not docs_readme_file.exists() or not docs_tech_file.exists():
        print("❌ Fehler: Dokumentationsdateien fehlen in docs/!")
        print(f"   Erwartet: {docs_readme_file}")
        print(f"   Erwartet: {docs_tech_file}")
        return 1

    if not pap_xml_dir.exists() or not any(pap_xml_dir.glob("*.xml")):
        print("❌ Fehler: PAP-XML-Dateien fehlen!")
        print(f"   Erwartet XML-Dateien unter: {pap_xml_dir}")
        return 1

    # Build-Verzeichnis vorbereiten (u.a. für version_info.txt)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Versions- und Stand-Aktualisierung in Doku
    update_markdown_version(docs_readme_file, version_text, stand_text)
    update_markdown_version(docs_tech_file, version_text, stand_text)

    # Embedded Docs aus aktualisierter Doku neu erzeugen
    regenerate_embedded_docs(docs_readme_file, docs_tech_file, embedded_docs_file)

    # Version-Resource-Datei für EXE erzeugen
    write_windows_version_file(version_file, version_tuple, version_text, build_stamp)

    # Laufzeit-Version für GUI-Titelleiste erzeugen
    write_runtime_version_module(runtime_version_file, version_text, build_stamp)
    
    if not icon_file.exists():
        print(f"⚠️  Warnung: {icon_file} nicht gefunden. Build wird ohne Icon fortgesetzt.")
        icon_arg = None
    else:
        icon_arg = str(icon_file)
    
    print("=" * 70)
    print("LOHNSTEUERTABELLEN-ERSTELLER: EXE-BUILD")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print(f"Root: {root_dir}")
    print(f"GUI-Datei: {gui_file}")
    print(f"Icon: {icon_arg or '(keine)'}")
    print(f"PAP-XML: {pap_xml_dir}")
    print(f"Version: {version_text}")
    print(f"Versionsstatus: {version_state_file}")
    print(f"Stand: {stand_text}")
    print(f"Version-Info: {version_file}")
    print(f"Runtime-Version: {runtime_version_file}")
    print()
    
    # PyInstaller-Argumente
    pyinstaller_args = [
        str(gui_file),
        "--onefile",
        "--windowed",
        "--name=Lohnsteuertabellen-Ersteller",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
        f"--version-file={version_file}",
        "--collect-data=pandas",
        "--collect-data=openpyxl",
        "--collect-submodules=xlsxwriter",
        "--collect-submodules=openpyxl",
        "--exclude-module=pandas.tests",
        "--exclude-module=numpy.tests",
        "--exclude-module=pytest",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        f"--add-data={pap_xml_dir};data/pap_xml",
    ]
    
    # Icon optional
    if icon_arg:
        pyinstaller_args.insert(3, f"--icon={icon_arg}")
        pyinstaller_args.append(f"--add-data={icon_arg};.")
    
    print("PyInstaller wird gestartet…")
    print()
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
    except Exception as exc:
        print(f"❌ Build fehlgeschlagen: {exc}")
        return 1
    
    # Validierung
    exe_file = dist_dir / "Lohnsteuertabellen-Ersteller.exe"
    if exe_file.exists():
        save_version_state(version_state_file, version_tuple, build_stamp)
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        zip_file = create_release_zip(root_dir, docs_dir, exe_file, version_text)
        zip_size_mb = zip_file.stat().st_size / (1024 * 1024)
        print()
        print("=" * 70)
        print("✅ BUILD ERFOLGREICH")
        print("=" * 70)
        print(f"EXE-Datei: {exe_file}")
        print(f"Größe: {size_mb:.1f} MB")
        print(f"Release-ZIP: {zip_file}")
        print(f"ZIP-Größe: {zip_size_mb:.1f} MB")
        print(f"Build-Version: {version_text}")
        print()
        print("Start:")
        print(f"  {exe_file}")
        print("Release-Paket:")
        print(f"  {zip_file}")
        print()
        return 0
    else:
        print()
        print("❌ EXE-Datei nicht gefunden (Build ggf. fehlgeschlagen).")
        return 1


if __name__ == "__main__":
    sys.exit(build_exe())
