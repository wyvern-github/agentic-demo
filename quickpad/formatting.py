"""Formatting actions shared by the menu, toolbar, and editor."""

from PyQt6.QtCore import QObject, QSignalBlocker, Qt
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QKeySequence,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PyQt6.QtWidgets import QColorDialog, QFontComboBox, QMenu, QSpinBox, QToolBar

from .document import SafeTextEdit


class FormattingControls(QObject):
    def __init__(
        self, editor: SafeTextEdit, menu: QMenu, toolbar: QToolBar, parent: QObject
    ) -> None:
        super().__init__(parent)
        self.editor = editor

        self.bold_action = self._character_action(
            "&Bold", QKeySequence.StandardKey.Bold, self._set_bold
        )
        self.italic_action = self._character_action(
            "&Italic", QKeySequence.StandardKey.Italic, self._set_italic
        )
        self.underline_action = self._character_action(
            "&Underline", QKeySequence.StandardKey.Underline, self._set_underline
        )
        character_actions = [
            self.bold_action,
            self.italic_action,
            self.underline_action,
        ]
        menu.addActions(character_actions)
        toolbar.addSeparator()
        toolbar.addActions(character_actions)

        self.font_family = QFontComboBox(toolbar)
        self.font_family.setAccessibleName("Font family")
        self.font_family.setToolTip("Font family")
        self.font_family.setMaximumWidth(170)
        self.font_family.currentFontChanged.connect(self._set_font_family)
        toolbar.addWidget(self.font_family)

        self.font_size = QSpinBox(toolbar)
        self.font_size.setAccessibleName("Font size")
        self.font_size.setToolTip("Font size in points")
        self.font_size.setRange(1, 300)
        self.font_size.setSuffix(" pt")
        self.font_size.valueChanged.connect(self._set_font_size)
        toolbar.addWidget(self.font_size)

        self.color_action = QAction("Text &colour", self)
        self.color_action.triggered.connect(self._choose_color)
        menu.addAction(self.color_action)
        toolbar.addAction(self.color_action)

        menu.addSeparator()
        toolbar.addSeparator()
        group = QActionGroup(self)
        group.setExclusive(True)
        self.align_actions: dict[Qt.AlignmentFlag, QAction] = {}
        for label, alignment, shortcut in [
            ("Align &left", Qt.AlignmentFlag.AlignLeft, "Ctrl+L"),
            ("Align &centre", Qt.AlignmentFlag.AlignHCenter, "Ctrl+E"),
            ("Align &right", Qt.AlignmentFlag.AlignRight, "Ctrl+R"),
            ("&Justify", Qt.AlignmentFlag.AlignJustify, "Ctrl+J"),
        ]:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setShortcut(QKeySequence(shortcut))
            action.setToolTip(label.replace("&", ""))
            action.triggered.connect(
                lambda checked, value=alignment: self.editor.setAlignment(value)
            )
            group.addAction(action)
            menu.addAction(action)
            toolbar.addAction(action)
            self.align_actions[alignment] = action

        self.bullet_action = QAction("&Bullets", self)
        self.bullet_action.setCheckable(True)
        self.bullet_action.setToolTip("Toggle bulleted paragraphs")
        self.bullet_action.triggered.connect(self._set_bullets)
        menu.addAction(self.bullet_action)
        toolbar.addAction(self.bullet_action)

        editor.currentCharFormatChanged.connect(self._sync_controls)
        editor.cursorPositionChanged.connect(self._sync_controls)
        self._sync_controls()

    def _character_action(self, label, shortcut, handler) -> QAction:
        action = QAction(label, self)
        action.setCheckable(True)
        action.setShortcut(shortcut)
        action.setToolTip(label.replace("&", ""))
        action.triggered.connect(handler)
        return action

    def _merge(self, char_format: QTextCharFormat) -> None:
        self.editor.mergeCurrentCharFormat(char_format)

    def _set_bold(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Weight.Bold if enabled else QFont.Weight.Normal)
        self._merge(char_format)

    def _set_italic(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontItalic(enabled)
        self._merge(char_format)

    def _set_underline(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontUnderline(enabled)
        self._merge(char_format)

    def _set_font_family(self, font: QFont) -> None:
        char_format = QTextCharFormat()
        char_format.setFontFamilies([font.family()])
        self._merge(char_format)

    def _set_font_size(self, size: int) -> None:
        char_format = QTextCharFormat()
        char_format.setFontPointSize(float(size))
        self._merge(char_format)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(self.editor.textColor(), self.editor, "Text colour")
        if color.isValid():
            self._set_color(color)

    def _set_color(self, color: QColor) -> None:
        char_format = QTextCharFormat()
        char_format.setForeground(color)
        self._merge(char_format)

    def _set_bullets(self, enabled: bool) -> None:
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        if enabled:
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_format)
        else:
            document = self.editor.document()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            if end > start and document.findBlock(end).position() == end:
                end -= 1
            block = document.findBlock(start)
            while block.isValid() and block.position() <= end:
                next_block = block.next()
                if block.textList() is not None:
                    block_format = block.blockFormat()
                    block_format.setObjectIndex(-1)
                    QTextCursor(block).setBlockFormat(block_format)
                block = next_block
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
        self._sync_controls()

    def _sync_controls(self, *_args) -> None:
        font = self.editor.currentFont()
        self.bold_action.setChecked(font.bold())
        self.italic_action.setChecked(font.italic())
        self.underline_action.setChecked(font.underline())
        family_blocker = QSignalBlocker(self.font_family)
        size_blocker = QSignalBlocker(self.font_size)
        if self.font_family.findText(font.family()) >= 0:
            self.font_family.setCurrentFont(font)
        else:
            self.font_family.setEditText(font.family())
        self.font_size.setValue(round(font.pointSizeF()))
        del family_blocker, size_blocker
        self.color_action.setToolTip(f"Text colour: {self.editor.textColor().name()}")

        alignment = self.editor.alignment() & Qt.AlignmentFlag.AlignHorizontal_Mask
        action = self.align_actions.get(
            alignment, self.align_actions[Qt.AlignmentFlag.AlignLeft]
        )
        action.setChecked(True)
        self.bullet_action.setChecked(self.editor.textCursor().currentList() is not None)
