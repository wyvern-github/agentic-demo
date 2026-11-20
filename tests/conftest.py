"""Shared, isolated Qt fixtures for QuickPad tests."""

import pytest
from PyQt6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from quickpad.window import MainWindow


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    """Show an editor and make teardown independent of unsaved-change dialogs."""
    editor_window = MainWindow()

    def clear_modified(_widget: QWidget) -> None:
        editor_window.editor.document().setModified(False)

    qtbot.addWidget(editor_window, before_close_func=clear_modified)
    editor_window.show()
    qtbot.waitUntil(editor_window.editor.hasFocus)
    return editor_window
