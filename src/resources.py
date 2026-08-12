from pathlib import Path
import sys

"""
Mesmo que não use, ele precisa ser importado para que, caso acessemos
os recursos gerados pelo sistema de recursos do Qt, os recursos possam
ser usados.
"""
import resources_rc

from PySide6.QtGui import QIcon, QPixmap

# Caminhos relativos utilizados para testar icones

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
STYLES_DIR = ASSETS_DIR / "styles"

# Se for verdade, usaremos os ícones do sistema de geração de ícone do Qt
def is_system_using_qrc():
    raw_arguments = sys.argv[1:]
    if "--use-qrc" in raw_arguments:
        return True
    
    return False

USE_QRC = is_system_using_qrc()

def _filesystem_path(*parts: str) -> str:
    """Returns an absolute filesystem path."""
    return str(ASSETS_DIR.joinpath(*parts))

# Utiliza o sistema de geração de icones compilados do Qt
def _qrc_path(*parts: str) -> str:
    """Returns a Qt Resource path."""
    return ":/" + "/".join(parts)

def _resource_path(*parts: str) -> str:
    """Returns either a filesystem path or a Qt Resource path."""

    if USE_QRC:
        return _qrc_path(*parts)

    return _filesystem_path(*parts)

def icon(name: str) -> QIcon:
    return QIcon(_resource_path("icons", name))


def pixmap(name: str) -> QPixmap:
    return QPixmap(_resource_path("icons", name))


def stylesheet(name: str) -> str:
    path = Path(_filesystem_path("styles", name))
    return path.read_text(encoding="utf-8")