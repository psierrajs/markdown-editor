from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTextEdit


class MarkdownTextEdit(QTextEdit):
    image_pasted = Signal(object)

    def insertFromMimeData(self, source):
        if source.hasImage():
            self.image_pasted.emit(source.imageData())
            return

        super().insertFromMimeData(source)