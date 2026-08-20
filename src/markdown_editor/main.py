import sys
from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file = None

        self.setWindowTitle("Markdown Editor")
        self.resize(900, 600)

        self.editor = QTextEdit()
        self.setCentralWidget(self.editor)

        self.create_menu()

    def create_menu(self):
        file_menu = self.menuBar().addMenu("File")

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("Markdown Editor")

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown file",
            "",
            "Markdown files (*.md);;All files (*)",
        )

        if not filename:
            return

        path = Path(filename)

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open file:\n{error}",
            )
            return

        self.editor.setPlainText(content)
        self.current_file = path
        self.setWindowTitle(f"{path.name} - Markdown Editor")

    def save_file(self):
        if self.current_file is None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Markdown file",
                "",
                "Markdown files (*.md);;All files (*)",
            )

            if not filename:
                return

            self.current_file = Path(filename)

        try:
            self.current_file.write_text(
                self.editor.toPlainText(),
                encoding="utf-8",
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not save file:\n{error}",
            )
            return

        self.setWindowTitle(
            f"{self.current_file.name} - Markdown Editor"
        )


def main():
    app = QApplication(sys.argv)

    window = MarkdownEditor()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()