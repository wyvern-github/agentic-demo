"""The QuickPad editor window and document lifecycle."""

from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QAction, QKeySequence, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QToolBar,
)

from quickpad.storage import (
    FILE_FILTERS,
    HTML_FILTER,
    TEXT_FILTER,
    DocumentFormat,
    read_document,
    save_target,
    write_document,
)


class LocalTextDocument(QTextDocument):
    """Keep rich text from loading local or remote external resources."""

    def loadResource(self, resource_type: int, name: QUrl) -> object:
        """Decline all resource requests, including images and stylesheets."""
        return None


def _remove_images(document: QTextDocument) -> None:
    image_ranges: list[tuple[int, int]] = []
    block = document.begin()
    while block.isValid():
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid() and fragment.charFormat().isImageFormat():
                image_ranges.append((fragment.position(), fragment.length()))
            iterator += 1
        block = block.next()

    cursor = QTextCursor(document)
    for position, length in reversed(image_ranges):
        cursor.setPosition(position)
        cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()


class MainWindow(QMainWindow):
    """Edit one local text or HTML document at a time."""

    def __init__(self) -> None:
        super().__init__()
        self.current_path: Path | None = None
        self.document_format = DocumentFormat.HTML

        self.editor = QTextEdit(self)
        self.editor.setObjectName("editor")
        self.editor.setAcceptRichText(False)
        self.editor.setDocument(LocalTextDocument(self.editor))
        self.setCentralWidget(self.editor)

        self.word_count = QLabel(self)
        self.statusBar().addPermanentWidget(self.word_count)
        self._create_actions()
        self._create_menus_and_toolbar()
        self.editor.textChanged.connect(self._update_word_count)
        self.editor.document().modificationChanged.connect(self._update_title)
        self._update_word_count()
        self._update_title()
        self.resize(1000, 700)
        self.setMinimumSize(640, 400)
        self.editor.setFocus()

    def _create_actions(self) -> None:
        self.new_action = QAction("&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_document)
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_document)
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_document)
        self.save_as_action = QAction("Save &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_as_document)

    def _create_menus_and_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addActions(
            [self.new_action, self.open_action, self.save_action, self.save_as_action]
        )
        toolbar = QToolBar("Document", self)
        toolbar.setObjectName("documentToolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.addActions([self.new_action, self.open_action, self.save_action])
        self.addToolBar(toolbar)

    def _update_word_count(self) -> None:
        count = len(self.editor.toPlainText().split())
        self.word_count.setText(f"Words: {count}")

    def _update_title(self, modified: bool | None = None) -> None:
        dirty = self.editor.document().isModified()
        name = self.current_path.name if self.current_path is not None else "Untitled"
        marker = "*" if dirty else ""
        self.setWindowTitle(f"{name}{marker} - QuickPad")
        self.setWindowModified(dirty)

    def _replace_contents(
        self, content: str, document_format: DocumentFormat, path: Path | None
    ) -> None:
        if document_format is DocumentFormat.HTML:
            self.editor.setHtml(content)
            _remove_images(self.editor.document())
        else:
            self.editor.setPlainText(content)
        document = self.editor.document()
        document.clearUndoRedoStacks()
        document.setModified(False)
        self.current_path = path
        self.document_format = document_format
        self._update_title()
        self._update_word_count()

    def new_document(self) -> None:
        """Replace the current document with a blank rich-text document."""
        self._replace_contents("", DocumentFormat.HTML, None)
        self.editor.setFocus()

    def open_document(self) -> bool:
        """Open a selected document, preserving the current one on failure."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open", "", FILE_FILTERS)
        if not filename:
            return False
        path = Path(filename)
        try:
            content, document_format = read_document(path)
        except (OSError, UnicodeError, ValueError) as error:
            QMessageBox.critical(self, "Cannot open document", f"Could not open {path}.\n{error}")
            return False
        self._replace_contents(content, document_format, path)
        self.editor.setFocus()
        return True

    def save_document(self) -> bool:
        """Save the current document, asking for a path when it is untitled."""
        if self.current_path is None:
            return self.save_as_document()
        return self._save_to(self.current_path, self.document_format)

    def save_as_document(self) -> bool:
        """Ask for a destination and save without changing state on failure."""
        selected = HTML_FILTER if self.document_format is DocumentFormat.HTML else TEXT_FILTER
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save As",
            str(self.current_path) if self.current_path is not None else "",
            FILE_FILTERS,
            selected,
        )
        if not filename:
            return False
        try:
            path, document_format = save_target(filename, selected_filter)
        except ValueError as error:
            QMessageBox.critical(self, "Cannot save document", str(error))
            return False
        return self._save_to(path, document_format)

    def _save_to(self, path: Path, document_format: DocumentFormat) -> bool:
        content = (
            self.editor.toHtml()
            if document_format is DocumentFormat.HTML
            else self.editor.toPlainText()
        )
        try:
            write_document(path, content)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Cannot save document", f"Could not save {path}.\n{error}")
            return False
        self.current_path = path
        self.document_format = document_format
        self.editor.document().setModified(False)
        self._update_title()
        self.statusBar().showMessage(f"Saved {path.name}", 3000)
        return True
