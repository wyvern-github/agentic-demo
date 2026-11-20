"""A keyboard-accessible, literal Find & Replace panel."""

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import (
    QKeySequence,
    QRegularExpressionValidator,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QWidget


class FindReplacePanel(QWidget):
    """Find and replace literal single-line text in an editor."""

    def __init__(self, editor: QTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.editor = editor
        self.find_input = QLineEdit(self)
        self.find_input.setAccessibleName("Find text")
        self.replace_input = QLineEdit(self)
        self.replace_input.setAccessibleName("Replacement text")
        single_line = QRegularExpression("[^\r\n\u2028\u2029]*")
        self.find_input.setValidator(QRegularExpressionValidator(single_line, self.find_input))
        self.replace_input.setValidator(
            QRegularExpressionValidator(single_line, self.replace_input)
        )

        find_label = QLabel("&Find:", self)
        find_label.setBuddy(self.find_input)
        replace_label = QLabel("&Replace:", self)
        replace_label.setBuddy(self.replace_input)
        self.find_button = QPushButton("Find &Next", self)
        self.replace_button = QPushButton("&Replace", self)
        self.replace_all_button = QPushButton("Replace &All", self)
        self.close_button = QPushButton("Close", self)
        self.status = QLabel(self)
        self.status.setAccessibleName("Find and replace status")

        layout = QGridLayout(self)
        layout.addWidget(find_label, 0, 0)
        layout.addWidget(self.find_input, 0, 1)
        layout.addWidget(self.find_button, 0, 2)
        layout.addWidget(self.close_button, 0, 3)
        layout.addWidget(replace_label, 1, 0)
        layout.addWidget(self.replace_input, 1, 1)
        layout.addWidget(self.replace_button, 1, 2)
        layout.addWidget(self.replace_all_button, 1, 3)
        layout.addWidget(self.status, 2, 0, 1, 4)
        layout.setColumnStretch(1, 1)

        self.find_input.textChanged.connect(self._update_controls)
        self.replace_input.textChanged.connect(self._update_controls)
        self.find_input.returnPressed.connect(self.find_next)
        self.replace_input.returnPressed.connect(self.replace_one)
        self.find_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_one)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.close_button.clicked.connect(self.close_panel)
        self.editor.textChanged.connect(self._document_changed)
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.close_panel)
        self._update_controls()

    def show_for_search(self) -> None:
        """Show the panel and focus the search field."""
        self.show()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def close_panel(self) -> None:
        """Hide the panel and return keyboard focus to the document."""
        self.hide()
        self.editor.setFocus()

    def _update_controls(self) -> None:
        query = self.find_input.text()
        valid_query = bool(query) and self.find_input.hasAcceptableInput()
        valid_replacement = self.replace_input.hasAcceptableInput()
        self.find_button.setEnabled(valid_query)
        self.replace_button.setEnabled(valid_query and valid_replacement)
        self.replace_all_button.setEnabled(valid_query and valid_replacement)
        if not query:
            self.status.setText("Enter text to search.")
        elif not valid_query or not valid_replacement:
            self.status.setText("Find and replacement text must each be a single line.")
        else:
            self.status.setText("Press Find Next.")

    def _document_changed(self) -> None:
        self._update_controls()

    def _query(self) -> str | None:
        if not self.find_input.text() or not self.find_input.hasAcceptableInput():
            self._update_controls()
            return None
        return self.find_input.text()

    def find_next(self) -> bool:
        """Select the next case-insensitive literal match, wrapping once."""
        query = self._query()
        if query is None:
            return False
        document = self.editor.document()
        start = QTextCursor(document)
        start.setPosition(self.editor.textCursor().selectionEnd())
        match = document.find(query, start)
        wrapped = False
        if match.isNull() and start.position() != 0:
            start.movePosition(QTextCursor.MoveOperation.Start)
            match = document.find(query, start)
            wrapped = not match.isNull()
        if match.isNull():
            self.status.setText("No matches found.")
            return False
        self.editor.setTextCursor(match)
        self.editor.ensureCursorVisible()
        self.status.setText("Match found (wrapped)." if wrapped else "Match found.")
        return True

    def _selection_matches(self, query: str) -> bool:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return False
        start = QTextCursor(self.editor.document())
        start.setPosition(cursor.selectionStart())
        match = self.editor.document().find(query, start)
        return (
            not match.isNull()
            and match.selectionStart() == cursor.selectionStart()
            and match.selectionEnd() == cursor.selectionEnd()
        )

    @staticmethod
    def _first_character_format(match: QTextCursor) -> QTextCharFormat:
        cursor = QTextCursor(match.document())
        cursor.setPosition(match.selectionStart())
        cursor.movePosition(
            QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor
        )
        return cursor.charFormat()

    def replace_one(self) -> bool:
        """Replace the selected match, or select the next one first."""
        query = self._query()
        if query is None or not self.replace_input.hasAcceptableInput():
            self._update_controls()
            return False
        if not self._selection_matches(query):
            self.find_next()
            return False
        cursor = self.editor.textCursor()
        cursor.insertText(self.replace_input.text(), self._first_character_format(cursor))
        self.editor.setTextCursor(cursor)
        self.status.setText("Replaced 1 occurrence.")
        return True

    def replace_all(self) -> int:
        """Replace all non-overlapping matches in one undoable edit."""
        query = self._query()
        if query is None or not self.replace_input.hasAcceptableInput():
            self._update_controls()
            return 0
        document = self.editor.document()
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        count = 0
        while True:
            match = document.find(query, cursor)
            if match.isNull():
                break
            match.insertText(self.replace_input.text(), self._first_character_format(match))
            cursor = match
            count += 1
        cursor.endEditBlock()
        if count:
            self.editor.setTextCursor(cursor)
            self.status.setText(f"Replaced {count} occurrence{'s' if count != 1 else ''}.")
        else:
            self.status.setText("No matches found.")
        return count
