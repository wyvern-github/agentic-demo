"""Shared widget fixture for QuickPad's behavioral tests."""

import pytest

from quickpad.main_window import MainWindow


@pytest.fixture
def window(qtbot):
    widget = MainWindow()
    qtbot.addWidget(
        widget,
        before_close_func=lambda current: current.editor.document().setModified(False),
    )
    widget.show()
    widget.editor.setFocus()
    return widget
