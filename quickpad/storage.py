"""Read and atomically write QuickPad's supported UTF-8 formats."""

from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QIODevice, QSaveFile


class DocumentFormat(Enum):
    """The document formats supported by the editor."""

    TEXT = ".txt"
    HTML = ".html"


TEXT_FILTER = "Text files (*.txt)"
HTML_FILTER = "HTML files (*.html)"
FILE_FILTERS = f"{HTML_FILTER};;{TEXT_FILTER}"


def format_for_path(path: Path) -> DocumentFormat:
    """Determine the format from an explicit supported file suffix."""
    try:
        return DocumentFormat(path.suffix.lower())
    except ValueError as error:
        raise ValueError("Choose a file with a .txt or .html extension.") from error


def save_target(filename: str, selected_filter: str) -> tuple[Path, DocumentFormat]:
    """Resolve a save dialog result without overriding an explicit suffix."""
    path = Path(filename)
    if path.suffix:
        return path, format_for_path(path)

    formats = {TEXT_FILTER: DocumentFormat.TEXT, HTML_FILTER: DocumentFormat.HTML}
    try:
        document_format = formats[selected_filter]
    except KeyError as error:
        raise ValueError("Choose the Text or HTML file type.") from error
    return path.with_name(path.name + document_format.value), document_format


def read_document(path: Path) -> tuple[str, DocumentFormat]:
    """Read a supported file as UTF-8, leaving decoding errors visible."""
    document_format = format_for_path(path)
    return path.read_text(encoding="utf-8"), document_format


def write_document(path: Path, content: str) -> None:
    """Atomically replace a file with UTF-8 content, or raise an error."""
    data = content.encode("utf-8")
    output = QSaveFile(str(path))
    output.setDirectWriteFallback(False)
    if not output.open(QIODevice.OpenModeFlag.WriteOnly):
        raise OSError(output.errorString())
    if output.write(data) != len(data):
        message = output.errorString()
        output.cancelWriting()
        raise OSError(f"Could not write the complete file: {message}")
    if not output.commit():
        raise OSError(output.errorString())
