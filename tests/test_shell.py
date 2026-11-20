"""Shell, document state, and editing behavior."""

from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QImage, QTextCursor
from PyQt6.QtWidgets import QApplication


def test_window_opens_with_usable_editor_and_standard_actions(window):
    assert window.width() >= 960
    assert window.height() >= 640
    assert window.centralWidget() is window.editor
    assert window.editor.accessibleName() == "Document editor"
    assert window.toolbar.accessibleName() == "Editing toolbar"
    assert [action.text() for action in window.menuBar().actions()] == [
        "&File",
        "&Edit",
        "F&ormat",
        "&Help",
    ]
    assert not window.editor.document().isModified()
    assert not window.undo_action.isEnabled()
    assert not window.redo_action.isEnabled()


def test_format_controls_stay_accessible_at_minimum_width(window, qtbot):
    window.resize(600, 400)
    qtbot.wait(30)
    assert window.formatting.font_family.isVisible()
    assert window.formatting.font_size.isVisible()
    assert window.format_menu.actions()
    assert window.editor.isVisible()


def test_typing_undo_and_redo_update_dirty_and_action_state(window, qtbot):
    qtbot.keyClicks(window.editor, "hello")
    assert window.editor.toPlainText() == "hello"
    assert window.editor.document().isModified()
    assert window.isWindowModified()
    assert window.undo_action.isEnabled()

    window.undo_action.trigger()
    assert window.editor.toPlainText() == ""
    assert not window.editor.document().isModified()
    assert not window.isWindowModified()
    assert window.redo_action.isEnabled()

    window.redo_action.trigger()
    assert window.editor.toPlainText() == "hello"
    assert window.editor.document().isModified()


def test_moving_the_caret_does_not_dirty_a_clean_document(window):
    window.editor.setPlainText("two words")
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    window.editor.moveCursor(QTextCursor.MoveOperation.NextWord)
    assert not window.editor.document().isModified()


def test_clipboard_images_are_rejected_and_html_is_pasted_as_text(window):
    clipboard = QApplication.clipboard()
    image = QMimeData()
    image.setImageData(QImage(2, 2, QImage.Format.Format_RGB32))
    clipboard.setMimeData(image)
    window.editor.paste()
    assert window.editor.toPlainText() == ""

    mixed = QMimeData()
    mixed.setText("safe text")
    mixed.setHtml('<img src="file:///not-allowed.png"><b>safe text</b>')
    clipboard.setMimeData(mixed)
    window.editor.paste()
    assert window.editor.toPlainText() == "safe text"
    assert "<img" not in window.editor.toHtml().lower()
    clipboard.clear()
