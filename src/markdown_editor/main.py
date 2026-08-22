import sys
from pathlib import Path

from markdown_it import MarkdownIt
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTextBrowser,
    QTextEdit,
)


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file = None
        self.is_modified = False
        self.current_folder = None

        self.setWindowTitle("Markdown Editor")
        self.resize(900, 600)

        self.markdown = MarkdownIt()

        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.document_modified)
        self.editor.textChanged.connect(self.update_preview)

        self.preview = QTextBrowser()

        self.file_list = QListWidget()
        self.file_list.setEnabled(True)
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.itemClicked.connect(self.open_file_from_sidebar)

        editor_splitter = QSplitter(Qt.Horizontal)
        editor_splitter.addWidget(self.editor)
        editor_splitter.addWidget(self.preview)
        editor_splitter.setSizes([450, 450])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.file_list)
        main_splitter.addWidget(editor_splitter)
        main_splitter.setSizes([200, 700])

        self.setCentralWidget(main_splitter)

        self.create_menu()
        self.update_window_title()
        self.statusBar()
        self.update_status_bar()

    def update_preview(self):
        markdown_text = self.editor.toPlainText()
        html = self.markdown.render(markdown_text)
        self.preview.setHtml(html)

    def create_menu(self):
        file_menu = self.menuBar().addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Folder",
            "",
        )

        if not folder:
            return

        self.current_folder = Path(folder)
        self.load_markdown_files()


    def load_markdown_files(self):
        self.file_list.clear()

        if self.current_folder is None:
            return

        markdown_files = sorted(
            self.current_folder.glob("*.md"),
            key=lambda path: path.name.lower(),
        )

        for path in markdown_files:
            item = QListWidgetItem(path.name)

            # Store the path as a normal string
            item.setData(Qt.UserRole, str(path))

            self.file_list.addItem(item)

    def open_file_from_sidebar(self, item):
        if not self.confirm_unsaved_changes():
            return

        path = Path(item.data(Qt.UserRole))

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

        self.update_preview()
        self.update_window_title()

    def document_modified(self):
        self.is_modified = True
        self.update_window_title()
        self.update_status_bar()

    def update_status_bar(self):
        text = self.editor.toPlainText()

        lines = text.count("\n") + 1 if text else 0
        words = len(text.split())

        if self.current_file is None:
            file_info = "Untitled"
        else:
            file_info = str(self.current_file)

        modified_info = "Modified" if self.is_modified else "Saved"

        self.statusBar().showMessage(
            f"{file_info}    |    {lines} lines    |    "
            f"{words} words    |    {modified_info}"
        )

    def update_window_title(self):
        if self.current_file is None:
            filename = "Untitled"
        else:
            filename = self.current_file.name

        marker = " *" if self.is_modified else ""
        self.setWindowTitle(f"{filename}{marker} - Markdown Editor")
        self.update_status_bar()

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
        self.update_preview()
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
        self.update_preview()
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
        if (
            self.current_folder is not None
            and path.parent == self.current_folder
        ):
            self.load_markdown_files()
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