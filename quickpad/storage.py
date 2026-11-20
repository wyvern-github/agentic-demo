"""UTF-8 document preparation and atomic file writes."""

import os
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QIODeviceBase, QSaveFile

from .html_safety import sanitize_html

UTF8_BOM = b"\xef\xbb\xbf"
SUPPORTED_SUFFIXES = {".txt", ".html"}


class StorageError(Exception):
    """A document could not be safely read or written."""


@dataclass(frozen=True)
class PreparedDocument:
    path: Path
    content: str
    is_html: bool
    has_bom: bool


def validate_path(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise StorageError("Only .txt and .html files are supported.")


def prepare_bytes(path: Path, data: bytes) -> PreparedDocument:
    validate_path(path)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise StorageError("The file is not valid UTF-8.") from error
    is_html = path.suffix.lower() == ".html"
    if is_html:
        text = sanitize_html(text)
    return PreparedDocument(path, text, is_html, data.startswith(UTF8_BOM))


def read_document(path: Path) -> PreparedDocument:
    validate_path(path)
    try:
        data = path.read_bytes()
    except (OSError, ValueError) as error:
        raise StorageError(str(error)) from error
    return prepare_bytes(path, data)


def same_path(first: Path, second: Path) -> bool:
    try:
        return os.path.samefile(first, second)
    except (OSError, ValueError):
        return os.path.normcase(os.path.abspath(first)) == os.path.normcase(os.path.abspath(second))


def target_has_bom(path: Path, current_path: Path | None, current_bom: bool) -> bool:
    if current_path is not None and same_path(path, current_path):
        return current_bom
    try:
        if path.is_file():
            with path.open("rb") as stream:
                return stream.read(len(UTF8_BOM)) == UTF8_BOM
    except (OSError, ValueError) as error:
        raise StorageError(str(error)) from error
    return False


def atomic_write(path: Path, data: bytes) -> None:
    writer = QSaveFile(str(path))
    writer.setDirectWriteFallback(False)
    if not writer.open(QIODeviceBase.OpenModeFlag.WriteOnly):
        raise StorageError(writer.errorString())
    try:
        if writer.write(data) != len(data):
            raise StorageError(writer.errorString())
        if not writer.commit():
            raise StorageError(writer.errorString())
    except Exception:
        if writer.isOpen():
            writer.cancelWriting()
        raise
