"""Find and replace behavior through the editor and non-modal dialog."""

import pytest

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from quickpad.text_service import find_matches


def test_find_next_is_case_insensitive_wraps_and_does_not_dirty(window):
    window.editor.setPlainText("Alpha beta ALPHA")
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    assert window.search.find_next("alpha") == (0, 5)
    assert window.editor.textCursor().selectedText() == "Alpha"
    assert window.search.find_next("alpha") == (11, 16)
    assert window.editor.textCursor().selectedText() == "ALPHA"
    assert window.search.find_next("alpha") == (0, 5)
    assert window.search.find_next("alpha", match_case=True) is None
    assert not window.editor.document().isModified()


def test_search_is_literal_and_case_option_is_respected():
    text = "A.b axb a.B"
    assert find_matches(text, "a.b") == [(0, 3), (8, 11)]
    assert find_matches(text, "a.b", match_case=True) == []
    assert find_matches(text, "a.B", match_case=True) == [(8, 11)]
    assert find_matches(text, "") == []


def test_dialog_find_replace_and_replace_all_are_separately_undoable(window, qtbot):
    window.editor.setPlainText("red RED red")
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    window.find_action.trigger()
    dialog = window.find_dialog
    assert dialog.isVisible()
    assert not dialog.isModal()
    assert dialog.find_input.accessibleName() == "Find text"
    dialog.find_input.setPlainText("red")
    dialog.replace_input.setPlainText("blue")
    assert dialog.status_label.text() == "3 matches"
    qtbot.mouseClick(dialog.find_button, Qt.MouseButton.LeftButton)
    assert window.search.selection_offsets() == (0, 3)
    assert dialog.status_label.text() == "Match 1 of 3"
    qtbot.mouseClick(dialog.replace_button, Qt.MouseButton.LeftButton)
    assert window.editor.toPlainText() == "blue RED red"
    qtbot.mouseClick(dialog.replace_all_button, Qt.MouseButton.LeftButton)
    assert window.editor.toPlainText() == "blue blue blue"
    assert dialog.status_label.text() == "Replaced 2"

    window.undo_action.trigger()
    assert window.editor.toPlainText() == "blue RED red"
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "red RED red"
    assert not window.editor.document().isModified()
    window.redo_action.trigger()
    window.redo_action.trigger()
    assert window.editor.toPlainText() == "blue blue blue"


def test_match_case_and_empty_query_update_status_without_editing(window):
    window.editor.setPlainText("one ONE one")
    window.editor.document().setModified(False)
    dialog = window.find_dialog
    dialog.find_input.setPlainText("one")
    assert dialog.status_label.text() == "3 matches"
    dialog.match_case.setChecked(True)
    assert dialog.status_label.text() == "2 matches"
    dialog.find_next()
    assert window.search.selection_offsets() == (0, 3)
    before_cursor = window.editor.textCursor()
    dialog.find_input.clear()
    dialog.replace_input.setPlainText("ignored")
    dialog.find_next()
    dialog.replace_one()
    dialog.replace_all()
    assert dialog.status_label.text() == "0 matches"
    assert window.editor.toPlainText() == "one ONE one"
    assert window.editor.textCursor().selectionStart() == before_cursor.selectionStart()
    assert window.editor.textCursor().selectionEnd() == before_cursor.selectionEnd()
    assert not window.editor.document().isModified()


def test_replace_starts_after_unrelated_selection_and_wraps(window):
    window.editor.setPlainText("cat dog cat")
    window.editor.document().setModified(False)
    cursor = window.editor.textCursor()
    cursor.setPosition(4)
    cursor.setPosition(7, QTextCursor.MoveMode.KeepAnchor)
    window.editor.setTextCursor(cursor)
    assert window.search.replace_one("cat", "fox")
    assert window.editor.toPlainText() == "cat dog fox"
    assert window.search.replace_one("cat", "fox")
    assert window.editor.toPlainText() == "fox dog fox"


def test_identical_replacements_leave_clean_document_without_undo(window):
    window.editor.setPlainText("same same")
    window.editor.document().setModified(False)
    assert window.search.replace_all("same", "same") == 2
    assert window.editor.toPlainText() == "same same"
    assert not window.editor.document().isModified()
    assert not window.undo_action.isEnabled()


def test_find_next_action_reuses_dialog_query(window):
    window.editor.setPlainText("one two one")
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    window.find_dialog.find_input.setPlainText("one")
    window.find_next_action.trigger()
    assert window.search.selection_offsets() == (0, 3)
    window.find_next_action.trigger()
    assert window.search.selection_offsets() == (8, 11)
    assert not window.editor.document().isModified()


def test_find_keyboard_shortcuts_work_in_editor_and_dialog(window, qtbot):
    window.editor.setPlainText("one two one")
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    window.activateWindow()
    window.editor.setFocus()
    qtbot.keyClick(window.editor, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    dialog = window.find_dialog
    assert dialog.isVisible()
    qtbot.keyClicks(dialog.find_input, "one")
    qtbot.keyClick(dialog.find_input, Qt.Key.Key_F3)
    assert window.search.selection_offsets() == (0, 3)
    qtbot.keyClick(dialog.find_input, Qt.Key.Key_F3)
    assert window.search.selection_offsets() == (8, 11)
    assert not window.editor.document().isModified()


@pytest.mark.parametrize("match_case", [False, True])
def test_find_from_inside_an_overlapping_match_and_replace_all(window, match_case):
    window.editor.setPlainText("banana")
    window.editor.document().setModified(False)
    cursor = window.editor.textCursor()
    cursor.setPosition(2)
    window.editor.setTextCursor(cursor)
    dialog = window.find_dialog
    dialog.find_input.setPlainText("ana")
    dialog.match_case.setChecked(match_case)

    dialog.find_next()
    assert window.search.selection_offsets() == (3, 6)
    assert dialog.status_label.text() == "Match 2 of 2"
    dialog.find_next()
    assert window.search.selection_offsets() == (1, 4)
    assert dialog.status_label.text() == "Match 1 of 2"
    dialog.find_next()
    assert window.search.selection_offsets() == (3, 6)
    assert dialog.status_label.text() == "Match 2 of 2"
    assert not window.editor.document().isModified()

    dialog.replace_input.setPlainText("X")
    dialog.replace_all()
    assert window.editor.toPlainText() == "bXna"
    assert dialog.status_label.text() == "Replaced 1"
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "banana"
    assert not window.editor.document().isModified()
