"""Formatting, undo, and safe conversion between HTML and text."""

from pathlib import Path

import pytest
from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QColorDialog, QFileDialog, QMessageBox
from pytestqt.qtbot import QtBot

import quickpad.window as window_module
from quickpad.storage import HTML_FILTER, TEXT_FILTER, DocumentFormat
from quickpad.window import MainWindow


def select_text(window: MainWindow, start: int, end: int) -> None:
    """Select a range using Qt document positions."""
    cursor = window.editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    window.editor.setTextCursor(cursor)


def format_at(window: MainWindow, position: int) -> QTextCharFormat:
    """Return the format of the character at a Qt document position."""
    cursor = QTextCursor(window.editor.document())
    cursor.setPosition(position)
    cursor.movePosition(
        QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor
    )
    return cursor.charFormat()


def test_character_controls_apply_to_selection_and_follow_cursor(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    window.editor.insertPlainText("alpha beta")
    select_text(window, 0, 5)
    window.bold_action.trigger()
    window.italic_action.trigger()
    window.underline_action.trigger()
    window.font_size.setValue(18)
    family = "Courier New"
    window.font_family.currentFontChanged.emit(QFont(family))
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#b02030"))
    window.color_action.trigger()

    styled = format_at(window, 1)
    plain = format_at(window, 7)
    assert styled.fontWeight() == QFont.Weight.Bold
    assert styled.fontItalic() and styled.fontUnderline()
    assert styled.fontPointSize() == 18
    assert styled.fontFamilies()[0] == family
    assert styled.foreground().color() == QColor("#b02030")
    assert plain.fontWeight() == QFont.Weight.Normal
    assert not plain.fontItalic() and not plain.fontUnderline()

    select_text(window, 8, 8)
    assert not window.bold_action.isChecked()
    select_text(window, 1, 1)
    assert window.bold_action.isChecked()
    assert window.italic_action.isChecked()
    assert window.underline_action.isChecked()
    assert window.font_size.value() == 18


def test_format_controls_apply_to_subsequent_typing(
    window: MainWindow, qtbot: QtBot
) -> None:
    window.bold_action.trigger()
    window.italic_action.trigger()
    qtbot.keyClicks(window.editor, "next")
    assert format_at(window, 0).fontWeight() == QFont.Weight.Bold
    assert format_at(window, 0).fontItalic()


@pytest.mark.parametrize(
    "alignment",
    [
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignHCenter,
        Qt.AlignmentFlag.AlignRight,
        Qt.AlignmentFlag.AlignJustify,
    ],
)
def test_alignment_applies_to_selected_paragraphs(
    window: MainWindow, alignment: Qt.AlignmentFlag
) -> None:
    window.editor.insertPlainText("first\nsecond\nthird")
    select_text(window, 2, 8)
    window.alignment_actions[alignment].trigger()
    block = window.editor.document().begin()
    for _ in range(2):
        assert block.blockFormat().alignment() & Qt.AlignmentFlag.AlignHorizontal_Mask == alignment
        block = block.next()
    assert block.blockFormat().alignment() & Qt.AlignmentFlag.AlignHorizontal_Mask in (
        Qt.AlignmentFlag(0),
        Qt.AlignmentFlag.AlignLeft,
    )
    assert window.alignment_actions[alignment].isChecked()


def test_bullets_toggle_selected_paragraphs_and_do_not_count_as_words(
    window: MainWindow,
) -> None:
    window.editor.insertPlainText("one\ntwo")
    select_text(window, 0, 7)
    window.bullets_action.trigger()
    first = window.editor.document().begin()
    assert first.textList() is not None
    assert first.next().textList() is not None
    assert window.word_count.text() == "Words: 2"

    window.bullets_action.trigger()
    first = window.editor.document().begin()
    assert first.textList() is None
    assert first.next().textList() is None
    window.undo_action.trigger()
    first = window.editor.document().begin()
    assert first.textList() is not None and first.next().textList() is not None


def test_undo_redo_shortcuts_and_formatting_edits(window: MainWindow, qtbot: QtBot) -> None:
    assert not window.undo_action.isEnabled()
    assert not window.redo_action.isEnabled()
    qtbot.keyClicks(window.editor, "hello")
    assert window.undo_action.isEnabled()
    qtbot.keyClick(window.editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert window.editor.toPlainText() == ""
    assert window.redo_action.isEnabled()
    qtbot.keyClick(window.editor, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    assert window.editor.toPlainText() == "hello"

    select_text(window, 0, 5)
    window.bold_action.trigger()
    assert format_at(window, 1).fontWeight() == QFont.Weight.Bold
    window.undo_action.trigger()
    assert format_at(window, 1).fontWeight() == QFont.Weight.Normal
    window.redo_action.trigger()
    assert format_at(window, 1).fontWeight() == QFont.Weight.Bold


def test_html_round_trip_preserves_supported_styles(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "styled.html"
    window.editor.insertPlainText("one\ntwo")
    select_text(window, 0, 7)
    window.bold_action.trigger()
    window.italic_action.trigger()
    window.underline_action.trigger()
    window.font_size.setValue(18)
    window.font_family.currentFontChanged.emit(QFont("Courier New"))
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#b02030"))
    window.color_action.trigger()
    window.alignment_actions[Qt.AlignmentFlag.AlignHCenter].trigger()
    window.bullets_action.trigger()
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    assert window.save_as_document()
    window.new_document()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    assert window.open_document()

    assert window.editor.toPlainText() == "one\ntwo"
    styled = format_at(window, 1)
    assert styled.fontWeight() == QFont.Weight.Bold
    assert styled.fontItalic() and styled.fontUnderline()
    assert styled.fontPointSize() == 18
    assert styled.fontFamilies()[0] == "Courier New"
    assert styled.foreground().color() == QColor("#b02030")
    first = window.editor.document().begin()
    assert first.textList() is not None and first.next().textList() is not None
    assert first.blockFormat().alignment() & Qt.AlignmentFlag.AlignHCenter
    assert window.word_count.text() == "Words: 2"


def test_cancel_and_confirm_lossy_text_conversion(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "existing.txt"
    path.write_text("original", encoding="utf-8")
    window.editor.insertPlainText("important")
    select_text(window, 0, 9)
    window.bold_action.trigger()
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), TEXT_FILTER)
    )
    choices: list[str] = []

    def cancel(*args: object) -> QMessageBox.StandardButton:
        choices.append("cancel")
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "question", cancel)
    assert not window.save_as_document()
    assert path.read_text(encoding="utf-8") == "original"
    assert window.current_path is None
    assert window.document_format is DocumentFormat.HTML
    assert window.editor.document().isModified()
    assert format_at(window, 0).fontWeight() == QFont.Weight.Bold

    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    assert window.save_as_document()
    assert choices == ["cancel"]
    assert path.read_text(encoding="utf-8") == "important"
    assert window.document_format is DocumentFormat.TEXT
    assert not window.editor.document().isModified()
    assert not window.editor.document().isUndoAvailable()
    assert format_at(window, 0).fontWeight() == QFont.Weight.Normal
    assert all(not action.isEnabled() for action in window.format_actions)
    assert not window.font_family.isEnabled() and not window.font_size.isEnabled()


@pytest.mark.parametrize("kind", ["color", "family", "size", "alignment", "bullets"])
def test_each_supported_style_requires_confirmation_before_text_conversion(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    kind: str,
) -> None:
    window.editor.insertPlainText("keep")
    select_text(window, 0, 4)
    if kind == "color":
        monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#b02030"))
        window.color_action.trigger()
    elif kind == "family":
        window.font_family.currentFontChanged.emit(QFont("Courier New"))
    elif kind == "size":
        window.font_size.setValue(21)
    elif kind == "alignment":
        window.alignment_actions[Qt.AlignmentFlag.AlignHCenter].trigger()
    else:
        window.bullets_action.trigger()
    destination = tmp_path / "note.txt"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(destination), TEXT_FILTER)
    )
    prompts: list[str] = []

    def cancel(*args: object) -> QMessageBox.StandardButton:
        prompts.append("asked")
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "question", cancel)
    assert not window.save_as_document()
    assert prompts == ["asked"]
    assert not destination.exists()
    assert window.editor.toPlainText() == "keep"


def test_failed_text_conversion_keeps_original_rich_state(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original = tmp_path / "original.html"
    destination = tmp_path / "destination.txt"
    destination.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(original), HTML_FILTER)
    )
    window.editor.insertPlainText("styled")
    assert window.save_as_document()
    select_text(window, 0, 6)
    window.italic_action.trigger()
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(destination), TEXT_FILTER)
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes
    )
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, text: errors.append(text)
    )

    def fail_write(path: Path, content: str) -> None:
        raise OSError("write failed")

    monkeypatch.setattr(window_module, "write_document", fail_write)
    assert not window.save_as_document()
    assert destination.read_text(encoding="utf-8") == "keep"
    assert window.current_path == original
    assert window.document_format is DocumentFormat.HTML
    assert window.editor.document().isModified()
    assert format_at(window, 0).fontItalic()
    assert errors and "write failed" in errors[0]


def test_plain_open_disables_formatting_and_html_save_reenables_it(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, qtbot: QtBot
) -> None:
    plain = tmp_path / "note.txt"
    plain.write_text("plain", encoding="utf-8")
    html = tmp_path / "note.html"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(plain), ""))
    assert window.open_document()
    assert all(not action.isEnabled() for action in window.format_actions)
    window.bold_action.trigger()
    qtbot.keyClick(window.editor, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
    qtbot.keyClicks(window.editor, "x")
    assert format_at(window, 0).fontWeight() == QFont.Weight.Normal
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(html), HTML_FILTER)
    )
    assert window.save_as_document()
    assert all(action.isEnabled() for action in window.format_actions)
    assert window.font_family.isEnabled() and window.font_size.isEnabled()


def test_unformatted_text_save_clears_pending_insertion_style(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "empty.txt"
    window.bold_action.trigger()
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), TEXT_FILTER)
    )
    assert window.save_as_document()
    window.editor.insertPlainText("plain")
    assert format_at(window, 0).fontWeight() == QFont.Weight.Normal


def test_unformatted_text_save_preserves_undo_history(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "plain.txt"
    window.editor.insertPlainText("plain")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), TEXT_FILTER)
    )
    assert window.save_as_document()
    window.undo_action.trigger()
    assert window.editor.toPlainText() == ""
    window.redo_action.trigger()
    assert window.editor.toPlainText() == "plain"


def test_new_and_plain_open_do_not_inherit_the_previous_character_style(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Discard
    )
    window.bold_action.trigger()
    window.editor.insertPlainText("bold")
    window.new_document()
    window.editor.insertPlainText("fresh")
    assert format_at(window, 0).fontWeight() == QFont.Weight.Normal

    select_text(window, 0, 5)
    window.bold_action.trigger()
    plain = tmp_path / "plain.txt"
    plain.write_text("opened", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(plain), ""))
    assert window.open_document()
    assert format_at(window, 0).fontWeight() == QFont.Weight.Normal


def test_rich_clipboard_is_pasted_as_plain_text(window: MainWindow) -> None:
    mime = QMimeData()
    mime.setText("pasted")
    mime.setHtml("<b>pasted</b>")
    window.editor.insertFromMimeData(mime)
    assert window.editor.toPlainText() == "pasted"
    assert format_at(window, 0).fontWeight() == QFont.Weight.Normal
