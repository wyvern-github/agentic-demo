"""Keyboard, literal search, and grouped replacement behavior."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from pytestqt.qtbot import QtBot

from quickpad.window import MainWindow


def test_find_and_replace_shortcuts_restore_editor_focus(
    window: MainWindow, qtbot: QtBot
) -> None:
    window.editor.insertPlainText("one two")
    qtbot.keyClick(window.editor, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    panel = window.find_panel
    assert panel.isVisible()
    assert panel.find_input.hasFocus()
    qtbot.keyClicks(panel.find_input, "two")
    qtbot.keyClick(panel.find_input, Qt.Key.Key_Return)
    assert window.editor.textCursor().selectedText() == "two"
    qtbot.keyClick(panel.find_input, Qt.Key.Key_Escape)
    assert not panel.isVisible()
    assert window.editor.hasFocus()

    qtbot.keyClick(window.editor, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
    assert panel.isVisible()
    assert panel.find_input.hasFocus()
    qtbot.mouseClick(panel.close_button, Qt.MouseButton.LeftButton)
    assert not panel.isVisible()
    assert window.editor.hasFocus()


def test_search_panel_remains_usable_at_minimum_window_size(
    window: MainWindow, qtbot: QtBot
) -> None:
    window.resize(window.minimumSize())
    window.find_panel.show_for_search()
    qtbot.waitUntil(lambda: window.find_panel.isVisible())
    panel = window.find_panel
    for widget in (
        panel.find_input,
        panel.replace_input,
        panel.find_button,
        panel.replace_button,
        panel.replace_all_button,
        panel.close_button,
    ):
        assert widget.width() > 0
        assert panel.rect().contains(widget.geometry())
    assert window.editor.height() > 100


def test_empty_and_multiline_queries_disable_operations(window: MainWindow) -> None:
    panel = window.find_panel
    panel.show_for_search()
    assert not panel.find_button.isEnabled()
    assert not panel.replace_button.isEnabled()
    assert not panel.replace_all_button.isEnabled()
    assert "Enter text" in panel.status.text()

    panel.find_input.setText("two\nlines")
    assert not panel.find_button.isEnabled()
    assert not panel.replace_button.isEnabled()
    assert "single line" in panel.status.text()
    panel.find_input.setText("valid")
    panel.replace_input.setText("bad\nreplacement")
    assert panel.find_button.isEnabled()
    assert not panel.replace_button.isEnabled()
    assert not panel.replace_all_button.isEnabled()
    panel.replace_input.clear()
    assert panel.replace_button.isEnabled()
    assert panel.replace_all_button.isEnabled()


def test_find_next_is_case_insensitive_literal_and_wraps(window: MainWindow) -> None:
    window.editor.insertPlainText("Alpha [.*] alpha\nALPHA")
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    panel = window.find_panel
    panel.show_for_search()
    panel.find_input.setText("aLpHa")
    for expected in ("Alpha", "alpha", "ALPHA"):
        assert panel.find_next()
        assert window.editor.textCursor().selectedText() == expected
    assert panel.find_next()
    assert window.editor.textCursor().selectedText() == "Alpha"
    assert "wrapped" in panel.status.text()

    panel.find_input.setText("[.*]")
    assert panel.find_next()
    assert window.editor.textCursor().selectedText() == "[.*]"
    panel.find_input.setText("missing")
    assert not panel.find_next()
    assert panel.status.text() == "No matches found."


def test_replace_changes_only_the_selected_match(window: MainWindow) -> None:
    window.editor.insertPlainText("Cat cat cat")
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    panel = window.find_panel
    panel.find_input.setText("cAt")
    panel.replace_input.setText("dog")
    assert panel.find_next()
    assert panel.replace_one()
    assert window.editor.toPlainText() == "dog cat cat"
    assert panel.status.text() == "Replaced 1 occurrence."

    assert not panel.replace_one()
    assert window.editor.toPlainText() == "dog cat cat"
    assert window.editor.textCursor().selectedText() == "cat"
    assert panel.replace_one()
    assert window.editor.toPlainText() == "dog dog cat"


def test_empty_replacement_deletes_a_selected_match(window: MainWindow) -> None:
    window.editor.insertPlainText("one two")
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    panel = window.find_panel
    panel.find_input.setText("one")
    panel.replace_input.clear()
    assert panel.find_next()
    assert panel.replace_one()
    assert window.editor.toPlainText() == " two"
    assert window.word_count.text() == "Words: 1"
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "one two"


def test_replace_all_with_non_bmp_text_is_one_undoable_edit(window: MainWindow) -> None:
    original = "\U0001f600 alpha \U0001f642 ALPHA alpha"
    window.editor.insertPlainText(original)
    window.editor.document().clearUndoRedoStacks()
    panel = window.find_panel
    panel.find_input.setText("alpha")
    panel.replace_input.setText("new words")
    assert panel.replace_all() == 3
    assert window.editor.toPlainText() == "\U0001f600 new words \U0001f642 new words new words"
    assert panel.status.text() == "Replaced 3 occurrences."
    assert window.word_count.text() == "Words: 8"

    window.undo_action.trigger()
    assert window.editor.toPlainText() == original
    assert window.word_count.text() == "Words: 5"
    assert not window.undo_action.isEnabled()
    window.redo_action.trigger()
    assert window.editor.toPlainText() == "\U0001f600 new words \U0001f642 new words new words"
    assert window.word_count.text() == "Words: 8"


def test_empty_replacement_deletes_matches_and_can_be_undone(window: MainWindow) -> None:
    window.editor.insertPlainText("one two ONE")
    window.editor.document().clearUndoRedoStacks()
    panel = window.find_panel
    panel.find_input.setText("one")
    panel.replace_input.clear()
    assert panel.replace_all() == 2
    assert window.editor.toPlainText() == " two "
    assert window.word_count.text() == "Words: 1"
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "one two ONE"


def test_replacement_containing_query_does_not_replace_itself(window: MainWindow) -> None:
    window.editor.insertPlainText("aA")
    panel = window.find_panel
    panel.find_input.setText("a")
    panel.replace_input.setText("aa")
    assert panel.replace_all() == 2
    assert window.editor.toPlainText() == "aaaa"


def test_no_matches_does_not_create_an_undo_step(window: MainWindow) -> None:
    window.editor.insertPlainText("untouched")
    window.editor.document().clearUndoRedoStacks()
    panel = window.find_panel
    panel.find_input.setText("missing")
    panel.replace_input.setText("new")
    assert panel.replace_all() == 0
    assert panel.status.text() == "No matches found."
    assert window.editor.toPlainText() == "untouched"
    assert not window.editor.document().isUndoAvailable()


def test_replacements_inherit_each_match_first_character_format(window: MainWindow) -> None:
    window.editor.insertPlainText("foo foo")
    cursor = window.editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
    window.editor.setTextCursor(cursor)
    window.bold_action.trigger()
    cursor.setPosition(4)
    cursor.setPosition(7, QTextCursor.MoveMode.KeepAnchor)
    window.editor.setTextCursor(cursor)
    window.italic_action.trigger()
    window.editor.document().clearUndoRedoStacks()

    panel = window.find_panel
    panel.find_input.setText("foo")
    panel.replace_input.setText("x")
    assert panel.replace_all() == 2
    assert window.editor.toPlainText() == "x x"
    first = QTextCursor(window.editor.document())
    first.setPosition(0)
    first.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
    second = QTextCursor(window.editor.document())
    second.setPosition(2)
    second.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
    assert first.charFormat().fontWeight() == QFont.Weight.Bold
    assert not first.charFormat().fontItalic()
    assert second.charFormat().fontItalic()
    assert second.charFormat().fontWeight() == QFont.Weight.Normal
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "foo foo"


@pytest.mark.parametrize("query", ["\U0001f600", "\u00e9CLAIR"])
def test_find_handles_non_bmp_and_unicode_case(window: MainWindow, query: str) -> None:
    window.editor.insertPlainText("\U0001f600 \u00c9clair")
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    window.find_panel.find_input.setText(query)
    assert window.find_panel.find_next()
    assert window.editor.textCursor().selectedText() in ("\U0001f600", "\u00c9clair")
