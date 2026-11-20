"""Editor widgets that never fetch document resources or paste images."""

from PyQt6.QtCore import QMimeData, QUrl
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QTextEdit


class SafeTextDocument(QTextDocument):
    def loadResource(self, resource_type: int, name: QUrl) -> None:
        return None


class SafeTextEdit(QTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDocument(SafeTextDocument(self))
        self.setAcceptRichText(False)
        self.setAccessibleName("Document editor")
        self.setAccessibleDescription("Edit the current document")

    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        return source.hasText()

    def insertFromMimeData(self, source: QMimeData) -> None:
        if source.hasText():
            self.insertPlainText(source.text())


def has_rich_content(editor: SafeTextEdit) -> bool:
    """Treat explicit formatting as lossy even when it matches the default."""
    block = editor.document().begin()
    while block.isValid():
        if block.textList() is not None or block.blockFormat().properties():
            return True
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid() and fragment.charFormat().properties():
                return True
            iterator += 1
        block = block.next()
    return False
