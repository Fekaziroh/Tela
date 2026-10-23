"""Writes the Windows version resource for Tela.exe (PyInstaller --version-file).

    python installer/version_info.py build/version_info.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import VERSION  # noqa: E402

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(filevers=({v}, 0), prodvers=({v}, 0), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1,
                    subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Tela!'),
      StringStruct('FileDescription', 'Tela! - sensor panel for the Turing Smart Screen'),
      StringStruct('FileVersion', '{s}'),
      StringStruct('InternalName', 'Tela'),
      StringStruct('LegalCopyright', 'MIT License - Tela! contributors'),
      StringStruct('OriginalFilename', 'Tela.exe'),
      StringStruct('ProductName', 'Tela!'),
      StringStruct('ProductVersion', '{s}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def text(version=VERSION):
    parts = [int(x) for x in version.split(".")] + [0, 0]
    return TEMPLATE.format(v=", ".join(str(p) for p in parts[:3]), s=version)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build/version_info.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text(), encoding="utf-8")
