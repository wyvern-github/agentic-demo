"""Document search and a non-modal, multiline find/replace dialog."""

from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QVBoxLayout,
)

from .document import SafeTextEdit
from .text_service import codepoint_to_qt, find_matches, qt_to_codepoint


class DocumentSearch:
    def __init__(self, editor: SafeTextEdit) -> None:
        self.editor = editor

    def selection_offsets(self) -> tuple[int, int]:
        text = self.editor.toPlainText()
        cursor = self.editor.textCursor()
        return (
            qt_to_codepoint(text, cursor.selectionStart()),
            qt_to_codepoint(text, cursor.selectionEnd()),
        )

    def find_next(self, query: str, *, match_case: bool = False) -> tuple[int, int] | None:
        text = self.editor.toPlainText()
        matches = find_matches(text, query, match_case=match_case, overlapping=True)
        if not matches:
            return None
        current_start, current_end = self.selection_offsets()
        search_start = (
            current_start + 1 if (current_start, current_end) in matches else current_end
        )
        match = next((span for span in matches if span[0] >= search_start), matches[0])
        cursor = self.editor.textCursor()
        cursor.setPosition(codepoint_to_qt(text, match[0]))
        cursor.setPosition(codepoint_to_qt(text, match[1]), QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()
        return match

    def replace_one(self, query: str, replacement: str, *, match_case: bool = False) -> bool:
        if not query:
            return False
        text = self.editor.toPlainText()
        start, end = self.selection_offsets()
        selected = text[start:end]
        matches_selection = bool(selected) and (
            selected == query if match_case else selected.casefold() == query.casefold()
        )
        if not matches_selection:
            if self.find_next(query, match_case=match_case) is None:
                return False
            text = self.editor.toPlainText()
            start, end = self.selection_offsets()
            selected = text[start:end]
        cursor = self.editor.textCursor()
        if selected == replacement:
            cursor.setPosition(codepoint_to_qt(text, end))
        else:
            cursor.beginEditBlock()
            cursor.insertText(replacement)
            cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        return True

    def replace_all(self, query: str, replacement: str, *, match_case: bool = False) -> int:
        text = self.editor.toPlainText()
        matches = find_matches(text, query, match_case=match_case)
        edits = [(start, end) for start, end in matches if text[start:end] != replacement]
        if edits:
            cursor = QTextCursor(self.editor.document())
            cursor.beginEditBlock()
            for start, end in reversed(edits):
                cursor.setPosition(codepoint_to_qt(text, start))
                cursor.setPosition(codepoint_to_qt(text, end), QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(replacement)
            cursor.endEditBlock()
            self.editor.setTextCursor(cursor)
        return len(matches)


class _PlainSearchInput(QPlainTextEdit):
    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        return source.hasText()

    def insertFromMimeData(self, source: QMimeData) -> None:
        if source.hasText():
            self.insertPlainText(source.text())


class FindReplaceDialog(QDialog):
    def __init__(self, search: DocumentSearch, parent=None) -> None:
        super().__init__(parent)
        self.search = search
        self.setWindowTitle("Find and replace")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumWidth(420)

        self.find_input = _PlainSearchInput(self)
        self.find_input.setAccessibleName("Find text")
        self.find_input.setPlaceholderText("Text to find; line breaks are supported")
        self.find_input.setTabChangesFocus(True)
        self.find_input.setFixedHeight(58)
        self.replace_input = _PlainSearchInput(self)
        self.replace_input.setAccessibleName("Replacement text")
        self.replace_input.setPlaceholderText("Replacement text")
        self.replace_input.setTabChangesFocus(True)
        self.replace_input.setFixedHeight(58)
        self.match_case = QCheckBox("Match &case", self)
        self.status_label = QLabel("0 matches", self)
        self.status_label.setAccessibleName("Search status")

        form = QFormLayout()
        form.addRow("&Find:", self.find_input)
        form.addRow("Replace &with:", self.replace_input)
        buttons = QHBoxLayout()
        self.find_button = QPushButton("Find &Next", self)
        self.replace_button = QPushButton("&Replace", self)
        self.replace_all_button = QPushButton("Replace &All", self)
        close_button = QPushButton("&Close", self)
        buttons.addWidget(self.find_button)
        buttons.addWidget(self.replace_button)
        buttons.addWidget(self.replace_all_button)
        buttons.addWidget(close_button)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.match_case)
        layout.addWidget(self.status_label)
        layout.addLayout(buttons)

        self.find_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_one)
        self.replace_all_button.clicked.connect(self.replace_all)
        close_button.clicked.connect(self.close)
        self.find_input.textChanged.connect(self._refresh_status)
        self.match_case.toggled.connect(self._refresh_status)
        self.search.editor.textChanged.connect(self._refresh_status)
        self.next_shortcut = QShortcut(QKeySequence("F3"), self)
        self.next_shortcut.activated.connect(self.find_next)

    def _refresh_status(self, *_args) -> None:
        matches = find_matches(
            self.search.editor.toPlainText(),
            self.find_input.toPlainText(),
            match_case=self.match_case.isChecked(),
            overlapping=True,
        )
        self.status_label.setText(f"{len(matches)} matches")

    def find_next(self) -> None:
        query = self.find_input.toPlainText()
        match_case = self.match_case.isChecked()
        match = self.search.find_next(query, match_case=match_case)
        if match is None:
            self.status_label.setText("0 matches")
            return
        matches = find_matches(
            self.search.editor.toPlainText(), query, match_case=match_case, overlapping=True
        )
        self.status_label.setText(f"Match {matches.index(match) + 1} of {len(matches)}")

    def replace_one(self) -> None:
        replaced = self.search.replace_one(
            self.find_input.toPlainText(),
            self.replace_input.toPlainText(),
            match_case=self.match_case.isChecked(),
        )
        self.status_label.setText("Replaced 1" if replaced else "0 matches")

    def replace_all(self) -> None:
        count = self.search.replace_all(
            self.find_input.toPlainText(),
            self.replace_input.toPlainText(),
            match_case=self.match_case.isChecked(),
        )
        self.status_label.setText(f"Replaced {count}" if count else "0 matches")
