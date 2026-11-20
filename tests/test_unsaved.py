"""Unsaved-change handling before destructive operations."""

import pytest

from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QFileDialog, QMessageBox


def choose(monkeypatch, response):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: response)


def test_new_cancel_retains_text_and_modified_state(window, monkeypatch):
    window.editor.insertPlainText("keep me")
    choose(monkeypatch, QMessageBox.StandardButton.Cancel)
    assert not window.new_document()
    assert window.editor.toPlainText() == "keep me"
    assert window.editor.document().isModified()
    assert window.undo_action.isEnabled()


def test_new_discard_creates_a_clean_empty_document(window, monkeypatch):
    window.editor.insertPlainText("discard me")
    choose(monkeypatch, QMessageBox.StandardButton.Discard)
    assert window.new_document()
    assert window.editor.toPlainText() == ""
    assert not window.editor.document().isModified()
    assert not window.undo_action.isEnabled()


def test_close_cancel_then_discard(window, monkeypatch):
    window.editor.insertPlainText("keep until confirmed")
    choose(monkeypatch, QMessageBox.StandardButton.Cancel)
    assert not window.close()
    assert window.isVisible()
    assert window.editor.toPlainText() == "keep until confirmed"
    choose(monkeypatch, QMessageBox.StandardButton.Discard)
    assert window.close()
    assert not window.isVisible()


def test_save_failure_aborts_new_without_a_pending_action(window, monkeypatch):
    window.editor.insertPlainText("keep")
    choose(monkeypatch, QMessageBox.StandardButton.Save)
    monkeypatch.setattr(window, "save_document", lambda: False)
    assert not window.new_document()
    assert window.editor.toPlainText() == "keep"
    choose(monkeypatch, QMessageBox.StandardButton.Discard)
    assert window.editor.toPlainText() == "keep"


@pytest.mark.parametrize("operation", ["new", "open", "close"])
@pytest.mark.parametrize(
    "choice",
    [
        QMessageBox.StandardButton.Save,
        QMessageBox.StandardButton.Discard,
        QMessageBox.StandardButton.Cancel,
    ],
)
def test_save_discard_cancel_for_each_replacement(
    window, monkeypatch, tmp_path, operation, choice
):
    target = tmp_path / "open.txt"
    target.write_text("opened", encoding="utf-8")
    saved = tmp_path / "saved.txt"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(saved), "Text files (*.txt)")
    )
    choose(monkeypatch, choice)
    window.editor.insertPlainText("original")
    result = {
        "new": window.new_document,
        "open": window.open_document,
        "close": window.close,
    }[operation]()

    if choice == QMessageBox.StandardButton.Cancel:
        assert not result
        assert window.editor.toPlainText() == "original"
        assert window.editor.document().isModified()
        assert window.current_path is None
        assert window.isVisible()
    else:
        assert result
        assert saved.exists() == (choice == QMessageBox.StandardButton.Save)
        if saved.exists():
            assert saved.read_text(encoding="utf-8") == "original"
        if operation == "new":
            assert window.editor.toPlainText() == ""
            assert window.current_path is None
        elif operation == "open":
            assert window.editor.toPlainText() == "opened"
            assert window.current_path == target
        else:
            assert not window.isVisible()


@pytest.mark.parametrize("operation", ["new", "open", "close"])
def test_failed_save_drops_replacement_request(window, monkeypatch, tmp_path, operation):
    target = tmp_path / "open.txt"
    target.write_text("opened", encoding="utf-8")
    failed = tmp_path / "missing" / "saved.txt"
    saved = tmp_path / "retry.txt"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(failed), "Text files (*.txt)")
    )
    errors = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: errors.append(args[1]))
    choose(monkeypatch, QMessageBox.StandardButton.Save)
    window.editor.insertPlainText("original")
    result = {
        "new": window.new_document,
        "open": window.open_document,
        "close": window.close,
    }[operation]()
    assert not result
    assert errors == ["Save failed"]
    assert window.editor.toPlainText() == "original"
    assert window.editor.document().isModified()
    assert window.current_path is None
    assert window.isVisible()

    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(saved), "Text files (*.txt)")
    )
    assert window.save_document()
    assert saved.read_text(encoding="utf-8") == "original"
    assert window.editor.toPlainText() == "original"
    assert window.isVisible()


@pytest.mark.parametrize("operation", ["new", "open", "close"])
def test_save_as_cancellation_aborts_replacement(window, monkeypatch, tmp_path, operation):
    target = tmp_path / "open.txt"
    target.write_text("opened", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    choose(monkeypatch, QMessageBox.StandardButton.Save)
    window.editor.insertPlainText("original")
    result = {
        "new": window.new_document,
        "open": window.open_document,
        "close": window.close,
    }[operation]()
    assert not result
    assert window.editor.toPlainText() == "original"
    assert window.editor.document().isModified()
    assert window.current_path is None
    assert window.isVisible()


def test_open_prepares_before_prompt_and_uses_same_target_saved_by_guard(
    window, monkeypatch, tmp_path
):
    target = tmp_path / "shared.txt"
    target.write_text("stale disk contents", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(target), "Text files (*.txt)")
    )
    choose(monkeypatch, QMessageBox.StandardButton.Save)
    window.editor.insertPlainText("new saved contents")
    assert window.open_document()
    assert target.read_text(encoding="utf-8") == "new saved contents"
    assert window.editor.toPlainText() == "new saved contents"
    assert window.current_path == target
    assert not window.editor.document().isModified()


def test_open_same_html_target_uses_newly_saved_formatted_content(window, monkeypatch, tmp_path):
    target = tmp_path / "shared.html"
    target.write_text("<p>stale</p>", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(target), "HTML files (*.html)")
    )
    choose(monkeypatch, QMessageBox.StandardButton.Save)
    window.editor.insertPlainText("new")
    cursor = window.editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    window.editor.setTextCursor(cursor)
    window.formatting.bold_action.trigger()
    assert window.open_document()
    assert window.editor.toPlainText() == "new"
    cursor = QTextCursor(window.editor.document())
    cursor.setPosition(1)
    assert cursor.charFormat().fontWeight() == QFont.Weight.Bold
    assert window.current_path == target


def test_open_cancel_retains_an_existing_document_path(window, monkeypatch, tmp_path):
    original = tmp_path / "original.txt"
    target = tmp_path / "other.txt"
    original.write_text("original", encoding="utf-8")
    target.write_text("other", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(original), ""))
    assert window.open_document()
    window.editor.moveCursor(QTextCursor.MoveOperation.End)
    window.editor.insertPlainText(" changed")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    choose(monkeypatch, QMessageBox.StandardButton.Cancel)
    assert not window.open_document()
    assert window.current_path == original
    assert window.editor.toPlainText() == "original changed"
    assert window.editor.document().isModified()


def test_open_cancel_and_invalid_utf8_never_prompt_or_change_document(window, monkeypatch, tmp_path):
    window.editor.insertPlainText("original")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[1]))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: ("", ""))
    assert not window.open_document()
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"\xff\xfe\x00")
    errors = []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(bad), ""))
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: errors.append(args[1]))
    assert not window.open_document()
    assert errors == ["Open failed"]
    assert warnings == []
    assert window.editor.toPlainText() == "original"
    assert window.editor.document().isModified()
    assert window.current_path is None


def test_new_resets_insertion_format(window, qtbot):
    window.formatting.bold_action.trigger()
    assert not window.editor.document().isModified()
    assert window.new_document()
    qtbot.keyClicks(window.editor, "x")
    cursor = QTextCursor(window.editor.document())
    cursor.setPosition(1)
    assert cursor.charFormat().fontWeight() == QFont.Weight.Normal
