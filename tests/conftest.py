"""Shared, isolated Qt fixtures for QuickPad tests."""

from collections.abc import Iterator

import pytest
from pytestqt.qtbot import QtBot

from quickpad.window import MainWindow


@pytest.fixture
def window(qtbot: QtBot) -> Iterator[MainWindow]:
    """Show an editor and make teardown independent of unsaved-change dialogs."""
    editor_window = MainWindow()
    qtbot.addWidget(editor_window)
    editor_window.show()
    qtbot.waitUntil(editor_window.editor.hasFocus)
    yield editor_window
    editor_window.editor.document().setModified(False)
