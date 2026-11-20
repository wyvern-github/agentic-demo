"""QuickPad's single-document window and unsaved-change guard."""

from pathlib import Path

from PyQt6.QtGui import QAction, QCloseEvent, QFont, QFontDatabase, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QToolBar

from .document import SafeTextEdit
from .formatting import FormattingControls


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_path: Path | None = None
        self.resize(960, 640)

        self.editor = SafeTextEdit(self)
        font = QApplication.font()
        if "Segoe UI" in QFontDatabase.families():
            font = QFont("Segoe UI", 11)
        self.editor.document().setDefaultFont(font)
        self.setCentralWidget(self.editor)

        self.file_menu = self.menuBar().addMenu("&File")
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.format_menu = self.menuBar().addMenu("F&ormat")
        self.help_menu = self.menuBar().addMenu("&Help")

        self.new_action = QAction("&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.setToolTip("Create a new document")
        self.new_action.triggered.connect(self.new_document)
        self.file_menu.addAction(self.new_action)

        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setToolTip("Undo the last change")
        self.undo_action.setEnabled(False)
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setToolTip("Redo the last change")
        self.redo_action.setEnabled(False)
        self.redo_action.triggered.connect(self.editor.redo)
        self.edit_menu.addActions([self.undo_action, self.redo_action])
        self.editor.document().undoAvailable.connect(self.undo_action.setEnabled)
        self.editor.document().redoAvailable.connect(self.redo_action.setEnabled)

        self.toolbar = QToolBar("Editing", self)
        self.toolbar.setObjectName("editingToolbar")
        self.toolbar.setAccessibleName("Editing toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self.toolbar.addActions([self.new_action, self.undo_action, self.redo_action])
        self.formatting = FormattingControls(
            self.editor, self.format_menu, self.toolbar, self
        )
        self.statusBar().showMessage("Ready")

        self.editor.document().modificationChanged.connect(self.setWindowModified)
        self._update_title()

    def _update_title(self) -> None:
        name = self.current_path.name if self.current_path else "Untitled"
        self.setWindowTitle(f"{name}[*] - QuickPad")
        self.setWindowModified(self.editor.document().isModified())

    def save_document(self) -> bool:
        """Return false until the file workflow is available."""
        return False

    def _may_replace_document(self) -> bool:
        if not self.editor.document().isModified():
            return True
        choice = QMessageBox.warning(
            self,
            "Unsaved changes",
            "Save changes to the current document?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self.save_document()
        return choice == QMessageBox.StandardButton.Discard

    def new_document(self) -> bool:
        if not self._may_replace_document():
            return False
        self.editor.clear()
        self.editor.document().setModified(False)
        self.current_path = None
        self._update_title()
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._may_replace_document():
            event.accept()
        else:
            event.ignore()
