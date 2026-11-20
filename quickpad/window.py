"""The QuickPad editor window and document lifecycle."""

from pathlib import Path

from PyQt6.QtCore import QSignalBlocker, QUrl, Qt
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QFont,
    QKeySequence,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextListFormat,
)
from PyQt6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QFontComboBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from quickpad.find_replace import FindReplacePanel
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


def _has_rich_formatting(document: QTextDocument) -> bool:
    if document.rootFrame().childFrames():
        return True
    default_font = document.defaultFont()
    block = document.begin()
    while block.isValid():
        block_format = block.blockFormat()
        alignment = block_format.alignment() & Qt.AlignmentFlag.AlignHorizontal_Mask
        if (
            block.textList() is not None
            or alignment not in (Qt.AlignmentFlag(0), Qt.AlignmentFlag.AlignLeft)
            or block_format.indent()
            or block_format.textIndent()
            or block_format.leftMargin()
            or block_format.rightMargin()
            or block_format.topMargin()
            or block_format.bottomMargin()
            or block_format.background().style() != Qt.BrushStyle.NoBrush
            or block_format.foreground().style() != Qt.BrushStyle.NoBrush
        ):
            return True
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid():
                char_format = fragment.charFormat()
                if (
                    char_format.font().resolve(default_font) != default_font
                    or char_format.foreground().style() != Qt.BrushStyle.NoBrush
                    or char_format.background().style() != Qt.BrushStyle.NoBrush
                    or char_format.isAnchor()
                    or char_format.verticalAlignment()
                    != QTextCharFormat.VerticalAlignment.AlignNormal
                ):
                    return True
            iterator += 1
        block = block.next()
    return False


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
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        self.find_panel = FindReplacePanel(self.editor, central)
        self.find_panel.hide()
        layout.addWidget(self.find_panel)
        layout.addWidget(self.editor, 1)
        self.setCentralWidget(central)

        self.word_count = QLabel(self)
        self.statusBar().addPermanentWidget(self.word_count)
        self._create_actions()
        self._create_menus_and_toolbar()
        self.editor.textChanged.connect(self._update_word_count)
        self.editor.document().modificationChanged.connect(self._update_title)
        self.editor.document().undoAvailable.connect(self.undo_action.setEnabled)
        self.editor.document().redoAvailable.connect(self.redo_action.setEnabled)
        self.editor.currentCharFormatChanged.connect(self._sync_format_controls)
        self.editor.cursorPositionChanged.connect(self._sync_format_controls)
        self._update_word_count()
        self._update_title()
        self._update_formatting_state()
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
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setEnabled(False)
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setEnabled(False)
        self.redo_action.triggered.connect(self.editor.redo)
        self.find_action = QAction("&Find...", self)
        self.find_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_action.triggered.connect(self.find_panel.show_for_search)
        self.replace_action = QAction("Find and &Replace...", self)
        self.replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        self.replace_action.triggered.connect(self.find_panel.show_for_search)

        self.bold_action = QAction("&Bold", self, checkable=True)
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.triggered.connect(self._set_bold)
        self.italic_action = QAction("&Italic", self, checkable=True)
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.triggered.connect(self._set_italic)
        self.underline_action = QAction("&Underline", self, checkable=True)
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.triggered.connect(self._set_underline)
        self.color_action = QAction("Text &colour...", self)
        self.color_action.triggered.connect(self._choose_color)

        self.alignment_group = QActionGroup(self)
        self.alignment_group.setExclusive(True)
        self.alignment_actions: dict[Qt.AlignmentFlag, QAction] = {}
        for label, alignment in (
            ("Align &left", Qt.AlignmentFlag.AlignLeft),
            ("Align &center", Qt.AlignmentFlag.AlignHCenter),
            ("Align &right", Qt.AlignmentFlag.AlignRight),
            ("&Justify", Qt.AlignmentFlag.AlignJustify),
        ):
            action = QAction(label, self, checkable=True)
            action.triggered.connect(
                lambda checked, value=alignment: self._set_alignment(value)
            )
            self.alignment_group.addAction(action)
            self.alignment_actions[alignment] = action
        self.bullets_action = QAction("Bulleted &list", self, checkable=True)
        self.bullets_action.triggered.connect(self._set_bullets)
        self.format_actions = [
            self.bold_action,
            self.italic_action,
            self.underline_action,
            self.color_action,
            *self.alignment_actions.values(),
            self.bullets_action,
        ]

    def _create_menus_and_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addActions(
            [self.new_action, self.open_action, self.save_action, self.save_as_action]
        )
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addActions([self.undo_action, self.redo_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.find_action, self.replace_action])
        format_menu = self.menuBar().addMenu("F&ormat")
        format_menu.addActions(
            [self.bold_action, self.italic_action, self.underline_action, self.color_action]
        )
        format_menu.addSeparator()
        format_menu.addActions(list(self.alignment_actions.values()))
        format_menu.addAction(self.bullets_action)

        self.toolbar = QToolBar("Document and formatting", self)
        self.toolbar.setObjectName("documentToolbar")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.addActions([self.new_action, self.open_action, self.save_action])
        self.toolbar.addSeparator()
        self.toolbar.addActions([self.undo_action, self.redo_action])
        self.toolbar.addSeparator()
        self.toolbar.addActions([self.bold_action, self.italic_action, self.underline_action])
        self.font_family = QFontComboBox(self.toolbar)
        self.font_family.setAccessibleName("Font family")
        self.font_family.setToolTip("Font family")
        self.font_family.currentFontChanged.connect(self._set_font_family)
        self.toolbar.addWidget(self.font_family)
        self.font_size = QSpinBox(self.toolbar)
        self.font_size.setRange(1, 512)
        self.font_size.setSuffix(" pt")
        self.font_size.setAccessibleName("Font size")
        self.font_size.setToolTip("Font size in points")
        self.font_size.valueChanged.connect(self._set_font_size)
        self.toolbar.addWidget(self.font_size)
        self.toolbar.addAction(self.color_action)
        self.toolbar.addSeparator()
        self.toolbar.addActions(list(self.alignment_actions.values()))
        self.toolbar.addAction(self.bullets_action)
        self.addToolBar(self.toolbar)

    def _merge_character_format(self, char_format: QTextCharFormat) -> None:
        self.editor.mergeCurrentCharFormat(char_format)

    def _set_bold(self, checked: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_character_format(char_format)

    def _set_italic(self, checked: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontItalic(checked)
        self._merge_character_format(char_format)

    def _set_underline(self, checked: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontUnderline(checked)
        self._merge_character_format(char_format)

    def _set_font_family(self, font: QFont) -> None:
        char_format = QTextCharFormat()
        char_format.setFontFamilies([font.family()])
        self._merge_character_format(char_format)

    def _set_font_size(self, size: int) -> None:
        char_format = QTextCharFormat()
        char_format.setFontPointSize(float(size))
        self._merge_character_format(char_format)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(self.editor.textColor(), self, "Text colour")
        if color.isValid():
            char_format = QTextCharFormat()
            char_format.setForeground(color)
            self._merge_character_format(char_format)

    def _set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        block_format = QTextBlockFormat()
        block_format.setAlignment(alignment)
        self.editor.textCursor().mergeBlockFormat(block_format)
        self._sync_format_controls()

    def _set_bullets(self, checked: bool) -> None:
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        if checked:
            cursor.createList(QTextListFormat.Style.ListDisc)
        else:
            document = self.editor.document()
            block = document.findBlock(cursor.selectionStart())
            end = cursor.selectionEnd()
            while block.isValid() and (
                block.position() < end or block.position() == cursor.selectionStart()
            ):
                next_block = block.next()
                text_list = block.textList()
                if text_list is not None:
                    text_list.remove(block)
                block = next_block
        cursor.endEditBlock()
        self._sync_format_controls()

    def _sync_format_controls(self, *_: object) -> None:
        char_format = self.editor.currentCharFormat()
        font = char_format.font().resolve(self.editor.document().defaultFont())
        self.bold_action.setChecked(font.weight() >= QFont.Weight.Bold)
        self.italic_action.setChecked(font.italic())
        self.underline_action.setChecked(font.underline())
        with QSignalBlocker(self.font_family), QSignalBlocker(self.font_size):
            self.font_family.setCurrentFont(font)
            self.font_size.setValue(round(font.pointSizeF()))
        alignment = self.editor.alignment() & Qt.AlignmentFlag.AlignHorizontal_Mask
        default_action = self.alignment_actions[Qt.AlignmentFlag.AlignLeft]
        self.alignment_actions.get(alignment, default_action).setChecked(True)
        self.bullets_action.setChecked(self.editor.textCursor().currentList() is not None)

    def _update_formatting_state(self) -> None:
        enabled = self.document_format is DocumentFormat.HTML
        for action in self.format_actions:
            action.setEnabled(enabled)
        self.font_family.setEnabled(enabled)
        self.font_size.setEnabled(enabled)
        self._sync_format_controls()

    def _update_word_count(self) -> None:
        count = len(self.editor.toPlainText().split())
        self.word_count.setText(f"Words: {count}")

    def _update_title(self, modified: bool | None = None) -> None:
        dirty = self.editor.document().isModified()
        name = self.current_path.name if self.current_path is not None else "Untitled"
        marker = "*" if dirty else ""
        self.setWindowTitle(f"{name}{marker} - QuickPad")

    def _replace_contents(
        self, content: str, document_format: DocumentFormat, path: Path | None
    ) -> None:
        document = self.editor.document()
        if document_format is DocumentFormat.HTML:
            document.setHtml(content)
            _remove_images(document)
        else:
            document.setPlainText(content)
        document.clearUndoRedoStacks()
        document.setModified(False)
        self.current_path = path
        self.document_format = document_format
        self._update_title()
        self._update_word_count()
        self._update_formatting_state()

    def _confirm_abandon(self) -> bool:
        if not self.editor.document().isModified():
            return True
        name = self.current_path.name if self.current_path is not None else "Untitled"
        choice = QMessageBox.warning(
            self,
            "Unsaved changes",
            f"Save changes to {name}?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self.save_document()
        return choice == QMessageBox.StandardButton.Discard

    def new_document(self) -> bool:
        """Create a blank document after resolving any unsaved changes."""
        if not self._confirm_abandon():
            return False
        self._replace_contents("", DocumentFormat.HTML, None)
        self.editor.setFocus()
        return True

    def open_document(self) -> bool:
        """Open a selected document, preserving the current one on failure."""
        if not self._confirm_abandon():
            return False
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

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prevent closing when unsaved changes have not been resolved."""
        if self._confirm_abandon():
            event.accept()
        else:
            event.ignore()

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
        changing_to_plain = (
            self.document_format is DocumentFormat.HTML
            and document_format is DocumentFormat.TEXT
        )
        lossy_conversion = (
            changing_to_plain and _has_rich_formatting(self.editor.document())
        )
        if lossy_conversion:
            choice = QMessageBox.question(
                self,
                "Save as plain text",
                "Plain text cannot retain formatting. Save without formatting?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return False
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
        if lossy_conversion:
            self._replace_contents(content, document_format, path)
        else:
            if changing_to_plain and not self.editor.textCursor().hasSelection():
                self.editor.setCurrentCharFormat(QTextCharFormat())
            self.current_path = path
            self.document_format = document_format
            self.editor.document().setModified(False)
            self._update_title()
            self._update_formatting_state()
        self.statusBar().showMessage(f"Saved {path.name}", 3000)
        return True
