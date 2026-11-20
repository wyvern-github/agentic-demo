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
