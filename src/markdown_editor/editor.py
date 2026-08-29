from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTextEdit


class MarkdownTextEdit(QTextEdit):
    image_pasted = Signal(object)
    image_dropped = Signal(str)

    IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".webp",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def insertFromMimeData(self, source):
        if source.hasImage():
            self.image_pasted.emit(source.imageData())
            return

        super().insertFromMimeData(source)

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            for url in mime_data.urls():
                if not url.isLocalFile():
                    continue

                path = Path(url.toLocalFile())

                if path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    event.acceptProposedAction()
                    return

        super().dragEnterEvent(event)

    def dropEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            for url in mime_data.urls():
                if not url.isLocalFile():
                    continue

                path = Path(url.toLocalFile())

                if path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    cursor = self.cursorForPosition(
                        event.position().toPoint()
                    )
                    self.setTextCursor(cursor)

                    self.image_dropped.emit(str(path))
                    event.acceptProposedAction()
                    return

        super().dropEvent(event)