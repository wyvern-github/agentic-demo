"""QuickPad's single-document window and unsaved-change guard."""

from pathlib import Path

from PyQt6.QtGui import (
    QAction, QCloseEvent, QFont, QFontDatabase, QKeySequence, QTextCharFormat,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox, QToolBar,
)

from . import storage
from .document import SafeTextEdit, has_rich_content
from .formatting import FormattingControls
from .html_safety import sanitize_html
from .search import DocumentSearch, FindReplaceDialog
from .text_service import word_count

FILE_FILTERS = "Text files (*.txt);;HTML files (*.html)"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_path: Path | None = None
        self._text_bom = False
        self._save_serial = 0
        self._last_save: tuple[Path, bytes] | None = None
        self.resize(960, 640)
        self.setMinimumSize(600, 400)

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
        self.about_action = QAction("&About QuickPad", self)
        self.about_action.triggered.connect(
            lambda: QMessageBox.about(self, "About QuickPad", "QuickPad is a small text editor.")
        )
        self.help_menu.addAction(self.about_action)

        self.new_action = QAction("&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.setToolTip("Create a new document")
        self.new_action.triggered.connect(self.new_document)
        self.file_menu.addAction(self.new_action)

        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setToolTip("Open a text or HTML document")
        self.open_action.triggered.connect(self.open_document)
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setToolTip("Save the current document")
        self.save_action.triggered.connect(self.save_document)
        self.save_as_action = QAction("Save &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_as)
        self.file_menu.addActions([self.open_action, self.save_action, self.save_as_action])
        self.file_menu.addSeparator()
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

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

        self.edit_menu.addSeparator()
        self.cut_action = QAction("Cu&t", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action = QAction("&Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action = QAction("&Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_all_action = QAction("Select &All", self)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.select_all_action.triggered.connect(self.editor.selectAll)
        self.edit_menu.addActions(
            [self.cut_action, self.copy_action, self.paste_action, self.select_all_action]
        )
        self.cut_action.setEnabled(False)
        self.copy_action.setEnabled(False)
        self.editor.copyAvailable.connect(self.cut_action.setEnabled)
        self.editor.copyAvailable.connect(self.copy_action.setEnabled)
        QApplication.clipboard().dataChanged.connect(self._sync_paste_action)
        self._sync_paste_action()

        self.search = DocumentSearch(self.editor)
        self.find_dialog = FindReplaceDialog(self.search, self)
        self.find_action = QAction("&Find...", self)
        self.find_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_action.triggered.connect(self.show_find_dialog)
        self.find_next_action = QAction("Find &Next", self)
        self.find_next_action.setShortcut(QKeySequence("F3"))
        self.find_next_action.triggered.connect(self._find_next)
        self.replace_action = QAction("&Replace...", self)
        self.replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        self.replace_action.triggered.connect(self.show_find_dialog)
        self.edit_menu.addSeparator()
        self.edit_menu.addActions(
            [self.find_action, self.find_next_action, self.replace_action]
        )

        self.toolbar = QToolBar("Editing", self)
        self.toolbar.setObjectName("editingToolbar")
        self.toolbar.setAccessibleName("Editing toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self.toolbar.addActions([self.new_action, self.undo_action, self.redo_action])
        self.toolbar.insertAction(self.undo_action, self.open_action)
        self.toolbar.insertAction(self.undo_action, self.save_action)
        self.addToolBarBreak()
        self.format_toolbar = QToolBar("Formatting", self)
        self.format_toolbar.setObjectName("formattingToolbar")
        self.format_toolbar.setAccessibleName("Formatting toolbar")
        self.format_toolbar.setMovable(False)
        self.addToolBar(self.format_toolbar)
        self.formatting = FormattingControls(
            self.editor, self.format_menu, self.format_toolbar, self
        )
        self.word_count_label = QLabel(self)
        self.word_count_label.setAccessibleName("Word count")
        self.word_count_label.setToolTip("Words in the current document")
        self.statusBar().addPermanentWidget(self.word_count_label)
        self.editor.textChanged.connect(self._update_word_count)
        self._update_word_count()
        self.statusBar().showMessage("Ready")

        self.editor.document().modificationChanged.connect(self.setWindowModified)
        self._update_title()
        self.editor.setFocus()

    def _sync_paste_action(self) -> None:
        self.paste_action.setEnabled(self.editor.canPaste())

    def _update_word_count(self) -> None:
        self.word_count_label.setText(f"Words: {word_count(self.editor.toPlainText())}")

    def show_find_dialog(self) -> None:
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()
        self.find_dialog.find_input.setFocus()

    def _find_next(self) -> None:
        if not self.find_dialog.find_input.toPlainText():
            self.show_find_dialog()
        else:
            self.find_dialog.find_next()

    def _update_title(self) -> None:
        name = self.current_path.name if self.current_path else "Untitled"
        self.setWindowTitle(f"{name}[*] - QuickPad")
        self.setWindowModified(self.editor.document().isModified())

    def save_document(self) -> bool:
        if self.current_path is None:
            return self.save_as()
        return self._save_to(self.current_path)

    def save_as(self) -> bool:
        initial = str(self.current_path) if self.current_path else ""
        filename, selected_filter = QFileDialog.getSaveFileName(
            self, "Save document", initial, FILE_FILTERS
        )
        if not filename:
            return False
        try:
            path = Path(filename)
            if not path.name:
                raise ValueError("Choose a file name.")
            if not path.suffix:
                suffix = ".html" if selected_filter.startswith("HTML") else ".txt"
                path = path.with_name(path.name + suffix)
        except ValueError as error:
            QMessageBox.critical(self, "Save failed", f"Could not save {filename}:\n{error}")
            return False
        return self._save_to(path)

    def _save_to(self, path: Path) -> bool:
        try:
            storage.validate_path(path)
            is_text = path.suffix.lower() == ".txt"
            rich = is_text and has_rich_content(self.editor)
            if rich:
                choice = QMessageBox.warning(
                    self,
                    "Formatting will be lost",
                    "Plain text cannot retain formatting. Save as plain text anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel,
                )
                if choice != QMessageBox.StandardButton.Yes:
                    return False
            if is_text:
                text = self.editor.toPlainText()
                bom = storage.target_has_bom(path, self.current_path, self._text_bom)
                data = (storage.UTF8_BOM if bom else b"") + text.encode("utf-8")
            else:
                bom = False
                html = sanitize_html(self.editor.toHtml(), preserve_qt_whitespace=True)
                data = html.encode("utf-8")
            storage.atomic_write(path, data)
        except (storage.StorageError, OSError, ValueError) as error:
            QMessageBox.critical(self, "Save failed", f"Could not save {path}:\n{error}")
            return False

        converting_html = self.current_path is not None and self.current_path.suffix.lower() == ".html"
        if is_text and (rich or converting_html):
            self._set_plain_text(text)
        self.editor.document().setModified(False)
        self.current_path = path
        self._text_bom = bom
        self._save_serial += 1
        self._last_save = (path, data)
        self._update_title()
        self.statusBar().showMessage("Saved", 3000)
        return True

    def open_document(self) -> bool:
        initial = str(self.current_path.parent) if self.current_path else ""
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self, "Open document", initial, FILE_FILTERS
        )
        if not filename:
            return False
        path = Path(filename)
        try:
            prepared = storage.read_document(path)
        except (storage.StorageError, OSError, ValueError) as error:
            QMessageBox.critical(self, "Open failed", f"Could not open {path}:\n{error}")
            return False
        previous_save = self._save_serial
        if not self._may_replace_document():
            return False
        if (
            self._save_serial != previous_save
            and self._last_save is not None
            and storage.same_path(path, self._last_save[0])
        ):
            prepared = storage.prepare_bytes(path, self._last_save[1])
        self._apply_document(prepared)
        return True

    def _set_plain_text(self, text: str) -> None:
        self.editor.clear()
        self.editor.setCurrentCharFormat(QTextCharFormat())
        self.editor.setPlainText(text)

    def _apply_document(self, prepared: storage.PreparedDocument) -> None:
        self.editor.clear()
        self.editor.setCurrentCharFormat(QTextCharFormat())
        if prepared.is_html:
            self.editor.setHtml(prepared.content)
        else:
            self.editor.setPlainText(prepared.content)
        self.editor.document().setModified(False)
        self.current_path = prepared.path
        self._text_bom = prepared.has_bom
        self._last_save = None
        self._update_title()
        self.statusBar().showMessage("Opened", 3000)

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
        self._set_plain_text("")
        self.editor.document().setModified(False)
        self.current_path = None
        self._text_bom = False
        self._last_save = None
        self._update_title()
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._may_replace_document():
            event.accept()
        else:
            event.ignore()
