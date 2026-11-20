"""Behavioral coverage for character and paragraph formatting."""

import pytest

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QTextCursor, QTextListFormat
from PyQt6.QtWidgets import QColorDialog


def select(editor, start, end):
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


def character_format(editor, index):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(index + 1)
    return cursor.charFormat()


@pytest.mark.parametrize(
    ("action_name", "property_name"),
    [
        ("bold_action", "fontWeight"),
        ("italic_action", "fontItalic"),
        ("underline_action", "fontUnderline"),
    ],
)
def test_character_actions_apply_to_selection_and_undo(
    window, action_name, property_name
):
    window.editor.setPlainText("plain styled")
    window.editor.document().setModified(False)
    select(window.editor, 6, 12)
    action = getattr(window.formatting, action_name)
    action.trigger()
    formatted = getattr(character_format(window.editor, 7), property_name)()
    plain = getattr(character_format(window.editor, 1), property_name)()
    if property_name == "fontWeight":
        assert formatted == QFont.Weight.Bold
        assert plain == QFont.Weight.Normal
    else:
        assert formatted and not plain
    assert window.editor.document().isModified()

    window.undo_action.trigger()
    assert not window.editor.document().isModified()
    reverted = getattr(character_format(window.editor, 7), property_name)()
    assert reverted == (QFont.Weight.Normal if property_name == "fontWeight" else False)
    window.redo_action.trigger()
    assert window.editor.document().isModified()


def test_insertion_format_does_not_dirty_until_typing(window, qtbot, monkeypatch):
    controls = window.formatting
    family = next(
        (
            name
            for name in QFontDatabase.families()
            if name.casefold() != window.editor.currentFont().family().casefold()
        ),
        "QuickPad Test Sans",
    )
    controls.bold_action.trigger()
    controls.italic_action.trigger()
    controls.underline_action.trigger()
    controls.font_family.setEditText(family)
    controls.font_size.setValue(18)
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#aa1122"))
    controls.color_action.trigger()
    assert not window.editor.document().isModified()
    assert not window.undo_action.isEnabled()

    window.editor.setFocus()
    qtbot.keyClicks(window.editor, "x")
    char_format = character_format(window.editor, 0)
    assert char_format.fontWeight() == QFont.Weight.Bold
    assert char_format.fontItalic()
    assert char_format.fontUnderline()
    assert char_format.fontFamilies() == [family]
    assert char_format.fontPointSize() == 18
    assert char_format.foreground().color() == QColor("#aa1122")
    window.undo_action.trigger()
    assert not window.editor.document().isModified()


def test_controls_follow_caret_without_dirtying_text(window, monkeypatch):
    window.editor.setPlainText("plain styled")
    select(window.editor, 6, 12)
    window.formatting.bold_action.trigger()
    window.formatting.italic_action.trigger()
    window.formatting.underline_action.trigger()
    window.formatting.font_family.setEditText("QuickPad Test Sans")
    window.formatting.font_size.setValue(20)
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor("#0088cc"))
    window.formatting.color_action.trigger()
    window.editor.document().setModified(False)

    select(window.editor, 2, 2)
    assert not window.formatting.bold_action.isChecked()
    assert not window.formatting.italic_action.isChecked()
    assert not window.formatting.underline_action.isChecked()
    assert window.formatting.font_family.currentText() != "QuickPad Test Sans"
    assert window.formatting.font_size.value() != 20
    select(window.editor, 8, 8)
    assert window.formatting.bold_action.isChecked()
    assert window.formatting.italic_action.isChecked()
    assert window.formatting.underline_action.isChecked()
    assert window.formatting.font_family.currentText() == "QuickPad Test Sans"
    assert window.formatting.font_size.value() == 20
    assert "#0088cc" in window.formatting.color_action.toolTip()
    assert character_format(window.editor, 8).fontFamilies() == ["QuickPad Test Sans"]
    assert not window.editor.document().isModified()


def test_cancelled_color_dialog_does_not_change_document(window, monkeypatch):
    window.editor.setPlainText("plain")
    window.editor.document().setModified(False)
    select(window.editor, 0, 5)
    monkeypatch.setattr(QColorDialog, "getColor", lambda *args: QColor())
    window.formatting.color_action.trigger()
    assert not window.editor.document().isModified()
    assert character_format(window.editor, 1).foreground().color() != QColor("#aa1122")


@pytest.mark.parametrize(
    "alignment",
    [
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignHCenter,
        Qt.AlignmentFlag.AlignRight,
        Qt.AlignmentFlag.AlignJustify,
    ],
)
def test_alignment_applies_to_selected_paragraphs(window, alignment):
    window.editor.setPlainText("first\nsecond")
    window.editor.document().setModified(False)
    select(window.editor, 0, len("first\nsecond"))
    window.formatting.align_actions[alignment].trigger()
    block = window.editor.document().begin()
    while block.isValid():
        assert block.blockFormat().alignment() & alignment
        block = block.next()
    assert window.formatting.align_actions[alignment].isChecked()


def test_alignment_controls_follow_paragraph_without_editing(window):
    window.editor.setPlainText("first\nsecond")
    select(window.editor, 7, 7)
    window.formatting.align_actions[Qt.AlignmentFlag.AlignRight].trigger()
    window.editor.document().setModified(False)
    select(window.editor, 2, 2)
    assert window.formatting.align_actions[Qt.AlignmentFlag.AlignLeft].isChecked()
    select(window.editor, 8, 8)
    assert window.formatting.align_actions[Qt.AlignmentFlag.AlignRight].isChecked()
    assert not window.editor.document().isModified()


def test_bullets_toggle_selected_paragraphs_and_are_undoable(window):
    window.editor.setPlainText("first\nsecond\nthird")
    window.editor.document().setModified(False)
    select(window.editor, 0, len("first\nsecond"))
    window.formatting.bullet_action.trigger()
    first = window.editor.document().begin()
    second = first.next()
    third = second.next()
    assert first.textList() is not None
    assert first.textList().format().style() == QTextListFormat.Style.ListDisc
    assert second.textList() is not None
    assert third.textList() is None
    select(window.editor, third.position(), third.position())
    assert not window.formatting.bullet_action.isChecked()
    select(window.editor, first.position(), first.position() + len("first\nsecond"))
    assert window.formatting.bullet_action.isChecked()

    window.formatting.bullet_action.trigger()
    assert first.textList() is None
    assert second.textList() is None
    assert first.blockFormat().indent() == second.blockFormat().indent() == 0
    window.undo_action.trigger()
    assert first.textList() is not None
    assert second.textList() is not None
    window.undo_action.trigger()
    assert first.textList() is None
    assert second.textList() is None
    assert not window.editor.document().isModified()
