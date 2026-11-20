"""File lifecycle, safe HTML, and word-count behavior."""

from pathlib import Path

import pytest
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from pytestqt.qtbot import QtBot

import quickpad.storage as storage
import quickpad.window as window_module
from quickpad.storage import HTML_FILTER, TEXT_FILTER, DocumentFormat
from quickpad.window import MainWindow


def test_launch_typing_and_new_reset_identity_and_history(
    window: MainWindow, qtbot: QtBot
) -> None:
    assert window.editor.hasFocus()
    assert window.windowTitle() == "Untitled - QuickPad"
    assert window.word_count.text() == "Words: 0"

    qtbot.keyClicks(window.editor, "alpha  beta")
    qtbot.keyClick(window.editor, Qt.Key.Key_Return)
    qtbot.keyClicks(window.editor, "gamma")
    assert window.word_count.text() == "Words: 3"
    assert window.windowTitle() == "Untitled* - QuickPad"
    assert window.editor.document().isUndoAvailable()

    window.new_action.trigger()
    assert window.editor.toPlainText() == ""
    assert window.current_path is None
    assert window.windowTitle() == "Untitled - QuickPad"
    assert window.word_count.text() == "Words: 0"
    assert not window.editor.document().isUndoAvailable()


@pytest.mark.parametrize(
    ("suffix", "selected_filter", "document_format"),
    [
        (".txt", HTML_FILTER, DocumentFormat.TEXT),
        (".html", TEXT_FILTER, DocumentFormat.HTML),
    ],
)
def test_save_and_open_round_trip(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    suffix: str,
    selected_filter: str,
    document_format: DocumentFormat,
) -> None:
    path = tmp_path / f"note{suffix}"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), selected_filter)
    )
    window.editor.insertPlainText("Alpha beta\ncaf\u00e9")

    window.save_action.trigger()
    assert path.is_file()
    assert window.current_path == path
    assert window.document_format is document_format
    assert not window.editor.document().isModified()
    assert window.windowTitle() == f"note{suffix} - QuickPad"

    window.new_action.trigger()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window.open_action.trigger()
    assert window.editor.toPlainText() == "Alpha beta\ncaf\u00e9"
    assert window.word_count.text() == "Words: 3"
    assert window.current_path == path
    assert not window.editor.document().isModified()

    window.editor.moveCursor(window.editor.textCursor().MoveOperation.End)
    window.editor.insertPlainText(" again")
    window.save_action.trigger()
    assert "again" in path.read_text(encoding="utf-8")
    assert not window.editor.document().isModified()


@pytest.mark.parametrize(
    ("name", "selected_filter", "expected_name", "document_format"),
    [
        ("untitled", HTML_FILTER, "untitled.html", DocumentFormat.HTML),
        ("untitled", TEXT_FILTER, "untitled.txt", DocumentFormat.TEXT),
        ("note.TXT", HTML_FILTER, "note.TXT", DocumentFormat.TEXT),
        ("note.html", TEXT_FILTER, "note.html", DocumentFormat.HTML),
    ],
)
def test_save_as_uses_filter_only_when_suffix_missing(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    name: str,
    selected_filter: str,
    expected_name: str,
    document_format: DocumentFormat,
) -> None:
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(tmp_path / name), selected_filter)
    )
    window.editor.insertPlainText("note")
    assert window.save_as_document()
    assert window.current_path == tmp_path / expected_name
    assert window.current_path.is_file()
    assert window.document_format is document_format


def test_canceled_dialogs_leave_document_unchanged(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.editor.insertPlainText("unsaved")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: ("", ""))
    assert not window.save_document()
    assert not window.open_document()
    assert window.editor.toPlainText() == "unsaved"
    assert window.current_path is None
    assert window.editor.document().isModified()


@pytest.mark.parametrize("operation", ["open", "save"])
def test_unsupported_suffix_reports_error_without_changing_document(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    operation: str,
) -> None:
    path = tmp_path / "note.md"
    path.write_text("existing", encoding="utf-8")
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, text: errors.append(text)
    )
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    window.editor.insertPlainText("unsaved")
    assert not (window.open_document() if operation == "open" else window.save_as_document())
    assert errors and ".txt or .html" in errors[0]
    assert path.read_text(encoding="utf-8") == "existing"
    assert window.editor.toPlainText() == "unsaved"
    assert window.current_path is None
    assert window.editor.document().isModified()


def test_invalid_utf8_and_read_failure_preserve_document(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    current = tmp_path / "current.txt"
    current.write_text("original ", encoding="utf-8")
    path = tmp_path / "invalid.txt"
    path.write_bytes(b"\xff")
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, text: errors.append(text)
    )
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(current), ""))
    assert window.open_document()
    window.editor.moveCursor(window.editor.textCursor().MoveOperation.End)
    window.editor.insertPlainText("keep me")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    assert not window.open_document()

    def fail_read(path: Path) -> tuple[str, DocumentFormat]:
        raise OSError("permission denied")

    monkeypatch.setattr(window_module, "read_document", fail_read)
    assert not window.open_document()
    assert len(errors) == 2 and "permission denied" in errors[-1]
    assert window.editor.toPlainText() == "original keep me"
    assert window.current_path == current
    assert window.editor.document().isModified()


def test_failed_atomic_write_preserves_destination_and_editor(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "existing.txt"
    path.write_text("original", encoding="utf-8")
    errors: list[str] = []
    real_save_file = storage.QSaveFile

    class ShortWrite:
        def __init__(self, filename: str) -> None:
            self.output = real_save_file(filename)

        def setDirectWriteFallback(self, enabled: bool) -> None:
            self.output.setDirectWriteFallback(enabled)

        def open(self, mode: object) -> bool:
            return self.output.open(mode)

        def write(self, data: bytes) -> int:
            self.output.write(data)
            return -1

        def errorString(self) -> str:
            return "injected write failure"

        def cancelWriting(self) -> None:
            self.output.cancelWriting()

    monkeypatch.setattr(storage, "QSaveFile", ShortWrite)
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, text: errors.append(text)
    )
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), TEXT_FILTER)
    )
    window.editor.insertPlainText("replacement")
    assert not window.save_as_document()
    assert path.read_text(encoding="utf-8") == "original"
    assert window.editor.toPlainText() == "replacement"
    assert window.current_path is None
    assert window.editor.document().isModified()
    assert errors and "injected write failure" in errors[0]


def test_open_html_discards_images_and_blocks_resources(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "images.html"
    path.write_text(
        '<p>before<img src="file:///not-a-file.png">'
        '<img src="https://example.invalid/picture.png">after</p>',
        encoding="utf-8",
    )
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    assert window.open_document()
    assert window.editor.toPlainText() == "beforeafter"
    assert "<img" not in window.editor.toHtml().lower()
    assert window.editor.document().loadResource(2, QUrl.fromLocalFile(str(path))) is None
    assert not window.editor.document().isModified()
