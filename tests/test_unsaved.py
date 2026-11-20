"""Unsaved-change handling before destructive operations."""

from PyQt6.QtWidgets import QMessageBox


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
