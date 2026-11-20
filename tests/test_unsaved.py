"""Unsaved-change decisions for New, Open, and Close."""

from pathlib import Path

import pytest
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QFileDialog, QMessageBox

import quickpad.window as window_module
from quickpad.storage import HTML_FILTER, TEXT_FILTER, DocumentFormat
from quickpad.window import MainWindow


def perform_operation(window: MainWindow, operation: str) -> bool:
    """Run one lifecycle action and report whether it completed."""
    if operation == "new":
        return window.new_document()
    if operation == "open":
        return window.open_document()
    return window.close()


@pytest.mark.parametrize("operation", ["new", "open", "close"])
@pytest.mark.parametrize(
    "choice",
    [
        QMessageBox.StandardButton.Save,
        QMessageBox.StandardButton.Discard,
        QMessageBox.StandardButton.Cancel,
    ],
)
def test_unsaved_decision_matrix(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    operation: str,
    choice: QMessageBox.StandardButton,
) -> None:
    save_path = tmp_path / "saved.html"
    open_path = tmp_path / "opened.txt"
    open_path.write_text("opened", encoding="utf-8")
    window.editor.insertPlainText("draft")
    prompts: list[str] = []
    open_calls: list[str] = []

    def decide(
        parent: object,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton,
        default: QMessageBox.StandardButton,
    ) -> QMessageBox.StandardButton:
        assert buttons == (
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        assert default == QMessageBox.StandardButton.Cancel
        prompts.append(text)
        return choice

    def choose_open(*args: object) -> tuple[str, str]:
        open_calls.append("open")
        return str(open_path), TEXT_FILTER

    monkeypatch.setattr(QMessageBox, "warning", decide)
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(save_path), HTML_FILTER)
    )
    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose_open)
    completed = perform_operation(window, operation)
    assert prompts == ["Save changes to Untitled?"]

    if choice == QMessageBox.StandardButton.Cancel:
        assert not completed
        assert window.isVisible()
        assert window.editor.toPlainText() == "draft"
        assert window.current_path is None
        assert window.editor.document().isModified()
        assert not save_path.exists()
        assert open_calls == []
        return

    assert completed
    if choice == QMessageBox.StandardButton.Save:
        assert "draft" in save_path.read_text(encoding="utf-8")
    else:
        assert not save_path.exists()
    if operation == "new":
        assert window.editor.toPlainText() == ""
        assert window.current_path is None
        assert not window.editor.document().isModified()
    elif operation == "open":
        assert window.editor.toPlainText() == "opened"
        assert window.current_path == open_path
        assert not window.editor.document().isModified()
        assert open_calls == ["open"]
    else:
        assert not window.isVisible()


@pytest.mark.parametrize("operation", ["new", "open", "close"])
def test_clean_document_proceeds_without_prompt(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, operation: str
) -> None:
    opened = tmp_path / "opened.txt"
    opened.write_text("opened", encoding="utf-8")
    window.editor.document().setPlainText("clean")
    window.editor.document().setModified(False)

    def unexpected_prompt(*args: object) -> QMessageBox.StandardButton:
        raise AssertionError("A clean document must not prompt")

    monkeypatch.setattr(QMessageBox, "warning", unexpected_prompt)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(opened), ""))
    assert perform_operation(window, operation)
    if operation == "new":
        assert window.editor.toPlainText() == ""
    elif operation == "open":
        assert window.editor.toPlainText() == "opened"
    else:
        assert not window.isVisible()


@pytest.mark.parametrize("operation", ["new", "open", "close"])
@pytest.mark.parametrize("failure", ["cancel_dialog", "write_error", "cancel_conversion"])
def test_unsuccessful_save_prevents_abandoning_document(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    operation: str,
    failure: str,
) -> None:
    window.editor.insertPlainText("draft")
    save_path = tmp_path / ("saved.txt" if failure == "cancel_conversion" else "saved.html")
    if failure == "cancel_conversion":
        save_path.write_text("keep", encoding="utf-8")
        window.editor.selectAll()
        window.bold_action.trigger()
    errors: list[str] = []
    open_calls: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Save
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, text: errors.append(text)
    )

    def choose_save(*args: object) -> tuple[str, str]:
        if failure == "cancel_dialog":
            return "", ""
        return str(save_path), TEXT_FILTER if failure == "cancel_conversion" else HTML_FILTER

    def choose_open(*args: object) -> tuple[str, str]:
        open_calls.append("unexpected")
        return "", ""

    def fail_write(path: Path, content: str) -> None:
        raise OSError("injected write failure")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", choose_save)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", choose_open)
    if failure == "write_error":
        monkeypatch.setattr(window_module, "write_document", fail_write)

    assert not perform_operation(window, operation)
    assert window.isVisible()
    assert window.editor.toPlainText() == "draft"
    assert window.current_path is None
    assert window.document_format is DocumentFormat.HTML
    assert window.editor.document().isModified()
    assert open_calls == []
    if failure == "write_error":
        assert errors and "injected write failure" in errors[0]
        assert not save_path.exists()
    elif failure == "cancel_conversion":
        assert save_path.read_text(encoding="utf-8") == "keep"
        assert window.editor.currentCharFormat().fontWeight() == QFont.Weight.Bold
    else:
        assert not errors and not save_path.exists()


@pytest.mark.parametrize("failure", ["cancel", "invalid_utf8"])
def test_discard_then_canceled_or_failed_open_keeps_current_document(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: str
) -> None:
    current = tmp_path / "current.txt"
    current.write_text("current ", encoding="utf-8")
    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(current), ""))
    assert window.open_document()
    window.editor.moveCursor(QTextCursor.MoveOperation.End)
    window.editor.insertPlainText("draft")
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Discard
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args: ("" if failure == "cancel" else str(invalid), ""),
    )
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda parent, title, text: errors.append(text)
    )
    assert not window.open_document()
    assert window.editor.toPlainText() == "current draft"
    assert window.current_path == current
    assert window.document_format is DocumentFormat.TEXT
    assert window.editor.document().isModified()
    assert bool(errors) == (failure == "invalid_utf8")


def test_failed_save_of_existing_file_keeps_identity_and_edits(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "current.html"
    window.editor.insertPlainText("saved")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    assert window.save_as_document()
    before = path.read_bytes()
    window.editor.insertPlainText(" changed")
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Save
    )
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: None)

    def fail_write(path: Path, content: str) -> None:
        raise OSError("injected write failure")

    monkeypatch.setattr(window_module, "write_document", fail_write)
    assert not window.new_document()
    assert path.read_bytes() == before
    assert window.current_path == path
    assert window.editor.toPlainText() == "saved changed"
    assert window.editor.document().isModified()


def test_format_only_edit_requires_confirmation(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "styled.html"
    window.editor.insertPlainText("text")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    assert window.save_as_document()
    window.editor.selectAll()
    window.bold_action.trigger()
    assert window.editor.document().isModified()
    prompts: list[str] = []

    def cancel(*args: object) -> QMessageBox.StandardButton:
        prompts.append("asked")
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "warning", cancel)
    assert not window.new_document()
    assert prompts == ["asked"]
    assert window.editor.toPlainText() == "text"
    assert window.editor.currentCharFormat().fontWeight() == QFont.Weight.Bold


def test_undo_back_to_saved_state_needs_no_prompt(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "saved.html"
    window.editor.insertPlainText("saved")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    assert window.save_as_document()
    window.editor.insertPlainText(" changed")
    assert window.editor.document().isModified()
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "saved"
    assert not window.editor.document().isModified()

    def unexpected_prompt(*args: object) -> QMessageBox.StandardButton:
        raise AssertionError("Returning to the saved state must not prompt")

    monkeypatch.setattr(QMessageBox, "warning", unexpected_prompt)
    assert window.new_document()


def test_undo_format_only_edit_returns_to_saved_state(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "saved.html"
    window.editor.insertPlainText("saved")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    assert window.save_as_document()
    window.editor.selectAll()
    window.italic_action.trigger()
    assert window.editor.document().isModified()
    window.undo_action.trigger()
    assert window.editor.toPlainText() == "saved"
    assert not window.editor.document().isModified()

    def unexpected_prompt(*args: object) -> QMessageBox.StandardButton:
        raise AssertionError("Undoing a format-only edit must restore the saved state")

    monkeypatch.setattr(QMessageBox, "warning", unexpected_prompt)
    assert window.new_document()


def test_replace_all_marks_document_unsaved_and_blocks_close(
    window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "saved.html"
    window.editor.insertPlainText("one one")
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: (str(path), HTML_FILTER)
    )
    assert window.save_as_document()
    window.find_panel.find_input.setText("one")
    window.find_panel.replace_input.setText("two")
    assert window.find_panel.replace_all() == 2
    assert window.editor.document().isModified()
    prompts: list[str] = []

    def cancel(*args: object) -> QMessageBox.StandardButton:
        prompts.append("asked")
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "warning", cancel)
    window.exit_action.trigger()
    assert prompts == ["asked"]
    assert window.isVisible()
    assert window.editor.toPlainText() == "two two"
