"""Unicode offsets, case folding, word counts, and live status."""

import pytest

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QFileDialog

from quickpad.text_service import (
    codepoint_to_qt, find_matches, qt_to_codepoint, word_count,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        ("hello,world!42", 3),
        ("e\u0301 e\u0301x \u0301", 2),
        ("Hi\U0001f60042\u0301... \u4f60\u597d", 3),
        ("\u0301 \u200d !! \U0001f600", 0),
        ("abc_123 \u2167", 3),
        ("\u4f60\u597d", 1),
    ],
)
def test_word_count_uses_unicode_letter_number_and_mark_runs(text, expected):
    assert word_count(text) == expected


def test_qt_positions_round_trip_after_supplementary_characters():
    text = "A\U0001f600B\ne\u0301"
    assert len(text) == 6
    assert codepoint_to_qt(text, len(text)) == 7
    assert codepoint_to_qt(text, 2) == 3
    for offset in range(len(text) + 1):
        assert qt_to_codepoint(text, codepoint_to_qt(text, offset)) == offset
    with pytest.raises(ValueError):
        qt_to_codepoint(text, 2)
    with pytest.raises(ValueError):
        codepoint_to_qt(text, len(text) + 1)


def test_cross_paragraph_find_and_replace_after_emoji_uses_codepoint_offsets(window):
    text = "\U0001f600Alpha\nBeta Z"
    window.editor.setPlainText(text)
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    dialog = window.find_dialog
    dialog.find_input.setPlainText("Alpha\nBeta")
    dialog.find_next()
    assert window.search.selection_offsets() == (1, 11)
    cursor = window.editor.textCursor()
    assert (cursor.selectionStart(), cursor.selectionEnd()) == (2, 12)
    assert cursor.selectedText().replace("\u2029", "\n") == "Alpha\nBeta"
    assert not window.editor.document().isModified()
    dialog.replace_input.setPlainText("X")
    dialog.replace_one()
    assert window.editor.toPlainText() == "\U0001f600X Z"
    window.undo_action.trigger()
    assert window.editor.toPlainText() == text
    assert not window.editor.document().isModified()


def test_casefold_expansion_never_selects_half_a_character(window):
    text = "Stra\u00dfe STRASSE"
    assert find_matches(text, "STRASSE") == [(0, 6), (7, 14)]
    assert find_matches("\u00df", "s") == []
    assert find_matches("\u00df", "ss") == [(0, 1)]
    assert find_matches("\u00dfs\u00df", "SSS", overlapping=True) == [(0, 2), (1, 3)]
    assert find_matches("\u00dfs\u00df", "SSS") == [(0, 2)]
    window.editor.setPlainText(text)
    window.editor.document().setModified(False)
    window.editor.moveCursor(QTextCursor.MoveOperation.Start)
    assert window.search.find_next("strasse") == (0, 6)
    assert window.editor.textCursor().selectedText() == "Stra\u00dfe"
    assert window.search.replace_one("strasse", "road")
    assert window.editor.toPlainText() == "road STRASSE"


def test_replace_all_with_emoji_is_one_undoable_edit(window):
    text = "\U0001f600a A\U0001f642a"
    window.editor.setPlainText(text)
    window.editor.document().setModified(False)
    assert window.search.replace_all("a", "\U0001f680") == 3
    assert window.editor.toPlainText() == "\U0001f600\U0001f680 \U0001f680\U0001f642\U0001f680"
    window.undo_action.trigger()
    assert window.editor.toPlainText() == text
    assert not window.editor.document().isModified()
    window.redo_action.trigger()
    assert window.editor.toPlainText() == "\U0001f600\U0001f680 \U0001f680\U0001f642\U0001f680"


def test_word_count_updates_after_edit_undo_open_and_new(window, monkeypatch, tmp_path):
    window.editor.setPlainText("One \U0001f600two")
    window.editor.document().setModified(False)
    assert window.word_count_label.text() == "Words: 2"
    window.editor.moveCursor(QTextCursor.MoveOperation.End)
    window.editor.insertPlainText(" three")
    assert window.word_count_label.text() == "Words: 3"
    window.undo_action.trigger()
    assert window.word_count_label.text() == "Words: 2"
    assert not window.editor.document().isModified()

    target = tmp_path / "count.txt"
    target.write_text("four,five\nsix", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(target), ""))
    assert window.open_document()
    assert window.word_count_label.text() == "Words: 3"
    assert window.new_document()
    assert window.word_count_label.text() == "Words: 0"
