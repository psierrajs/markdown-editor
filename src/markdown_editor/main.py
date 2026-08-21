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
        self.is_modified = False

        self.setWindowTitle("Markdown Editor")
        self.resize(900, 600)

        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.document_modified)
        self.setCentralWidget(self.editor)

        self.create_menu()
        self.update_window_title()

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

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

    def document_modified(self):
        self.is_modified = True
        self.update_window_title()

    def update_window_title(self):
        if self.current_file is None:
            filename = "Untitled"
        else:
            filename = self.current_file.name

        marker = " *" if self.is_modified else ""
        self.setWindowTitle(f"{filename}{marker} - Markdown Editor")

    def confirm_unsaved_changes(self):
        if not self.is_modified:
            return True

        response = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "The document has unsaved changes.\n\nDo you want to save them?",
            QMessageBox.Save
            | QMessageBox.Discard
            | QMessageBox.Cancel,
            QMessageBox.Save,
        )

        if response == QMessageBox.Save:
            return self.save_file()

        if response == QMessageBox.Discard:
            return True

        return False

    def new_file(self):
        if not self.confirm_unsaved_changes():
            return

        self.editor.blockSignals(True)
        self.editor.clear()
        self.editor.blockSignals(False)

        self.current_file = None
        self.is_modified = False
        self.update_window_title()

    def open_file(self):
        if not self.confirm_unsaved_changes():
            return

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

        self.editor.blockSignals(True)
        self.editor.setPlainText(content)
        self.editor.blockSignals(False)

        self.current_file = path
        self.is_modified = False
        self.update_window_title()

    def save_file(self):
        if self.current_file is None:
            return self.save_file_as()

        return self.write_file(self.current_file)

    def save_file_as(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown file",
            "",
            "Markdown files (*.md);;All files (*)",
        )

        if not filename:
            return False

        path = Path(filename)

        if path.suffix == "":
            path = path.with_suffix(".md")

        return self.write_file(path)

    def write_file(self, path):
        try:
            path.write_text(
                self.editor.toPlainText(),
                encoding="utf-8",
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not save file:\n{error}",
            )
            return False

        self.current_file = path
        self.is_modified = False
        self.update_window_title()
        return True

    def closeEvent(self, event):
        if self.confirm_unsaved_changes():
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)

    window = MarkdownEditor()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()