"""Launch the QuickPad desktop application."""

import sys

from PyQt6.QtWidgets import QApplication

from quickpad.window import MainWindow


def main() -> int:
    """Create the application and run its event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("QuickPad")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
