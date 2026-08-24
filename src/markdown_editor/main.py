import sys
import shutil
from markdown_editor.highlighter import MarkdownHighlighter
from pathlib import Path
from pathlib import Path
from PySide6.QtWidgets import QStyle

from markdown_it import MarkdownIt
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStyle,
    QTextBrowser,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
)

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        heading_format = QTextCharFormat()
        heading_format.setFontWeight(QFont.Weight.Bold)
        heading_format.setForeground(QColor("#4A90E2"))

        self.rules.append(
            (r"^#{1,6}\s.*$", heading_format)
        )

        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)

        self.rules.append(
            (r"\*\*[^*]+\*\*", bold_format)
        )

        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)

        self.rules.append(
            (r"\*[^*]+\*", italic_format)
        )

        code_format = QTextCharFormat()
        code_format.setFontFamily("monospace")
        code_format.setForeground(QColor("#C7254E"))

        self.rules.append(
            (r"`[^`]+`", code_format)
        )

        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#6A737D"))
        quote_format.setFontItalic(True)

        self.rules.append(
            (r"^>\s.*$", quote_format)
        )

        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#7B61FF"))

        self.rules.append(
            (r"^\s*[-*+]\s+", list_format)
        )

    def highlightBlock(self, text):
        import re

        for pattern, text_format in self.rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - match.start()

                self.setFormat(
                    start,
                    length,
                    text_format,
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
        editor_font = self.editor.font()
        editor_font.setPointSize(13)
        self.editor.setFont(editor_font)
        self.highlighter = MarkdownHighlighter(
            self.editor.document()
        )


        self.editor.textChanged.connect(self.document_modified)
        self.editor.textChanged.connect(self.update_preview)

        self.preview = QTextBrowser()

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.itemClicked.connect(self.open_file_from_sidebar)

        self.file_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.file_tree.customContextMenuRequested.connect(
            self.show_tree_context_menu
        )

        editor_splitter = QSplitter(Qt.Horizontal)
        editor_splitter.addWidget(self.editor)
        editor_splitter.addWidget(self.preview)
        editor_splitter.setSizes([450, 450])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.file_tree)
        main_splitter.addWidget(editor_splitter)
        main_splitter.setSizes([200, 700])

        self.setCentralWidget(main_splitter)

        self.create_menu()
        self.update_window_title()
        self.statusBar()
        self.update_status_bar()

    def increase_font_size(self):
        font = self.editor.font()
        font.setPointSize(font.pointSize() + 1)
        self.editor.setFont(font)


    def decrease_font_size(self):
        font = self.editor.font()

        if font.pointSize() > 8:
            font.setPointSize(font.pointSize() - 1)
            self.editor.setFont(font)


    def reset_font_size(self):
        font = self.editor.font()
        font.setPointSize(13)
        self.editor.setFont(font)

    def toggle_preview(self, checked):
        self.preview.setVisible(checked)

    def show_tree_context_menu(self, position):
        if self.current_folder is None:
            return

        item = self.file_tree.itemAt(position)

        if item is not None:
            self.file_tree.setCurrentItem(item)

        menu = QMenu(self)

        new_note_action = menu.addAction("New Note")
        new_folder_action = menu.addAction("New Folder")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        selected_action = menu.exec(
            self.file_tree.viewport().mapToGlobal(position)
        )

        if selected_action == new_note_action:
            self.create_new_note()

        elif selected_action == new_folder_action:
            self.create_new_folder()

        elif selected_action == rename_action:
            self.rename_selected_item()
        elif selected_action == delete_action:
            self.delete_selected_item()

    def delete_selected_item(self):
        selected_items = self.file_tree.selectedItems()

        if not selected_items:
            return

        item = selected_items[0]

        if item.parent() is None:
            QMessageBox.information(
                self,
                "Cannot Delete",
                "The root folder cannot be deleted from the application.",
            )
            return

        path_data = item.data(0, Qt.UserRole)

        if path_data is None:
            return

        path = Path(path_data)

        if path.is_dir():
            message = (
                f"Delete folder '{path.name}' and all of its contents?"
            )
        else:
            message = f"Delete '{path.name}'?"

        response = QMessageBox.warning(
            self,
            "Confirm Delete",
            message,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )

        if response != QMessageBox.Yes:
            return

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not delete item:\n{error}",
            )
            return

        if self.current_file == path:
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)

            self.current_file = None
            self.is_modified = False
            self.update_preview()
            self.update_window_title()

        self.load_markdown_files()

    def rename_selected_item(self):
        selected_items = self.file_tree.selectedItems()

        if not selected_items:
            return

        item = selected_items[0]

        if item.parent() is None:
            QMessageBox.information(
                self,
                "Cannot Rename",
                "The root folder cannot be renamed from the application.",
            )
            return

        path_data = item.data(0, Qt.UserRole)

        if path_data is None:
            return

        current_path = Path(path_data)

        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            "New name:",
            text=current_path.name,
        )

        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()

        if current_path.is_file():
            if current_path.suffix.lower() == ".md":
                if not new_name.lower().endswith(".md"):
                    new_name += ".md"

        new_path = current_path.parent / new_name

        if new_path == current_path:
            return

        if new_path.exists():
            QMessageBox.warning(
                self,
                "Name Already Exists",
                "An item with that name already exists.",
            )
            return

        try:
            current_path.rename(new_path)
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not rename item:\n{error}",
            )
            return

        if self.current_file == current_path:
            self.current_file = new_path

        self.load_markdown_files()
        self.update_window_title()


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

        new_note_action = QAction("New Note", self)
        new_note_action.triggered.connect(self.create_new_note)
        file_menu.addAction(new_note_action)

        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        file_menu.addAction(new_folder_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        view_menu = self.menuBar().addMenu("View")

        self.preview_action = QAction("Show Preview", self)
        self.preview_action.setCheckable(True)
        self.preview_action.setChecked(True)
        self.preview_action.triggered.connect(self.toggle_preview)

        view_menu.addSeparator()

        increase_font_action = QAction("Increase Font Size", self)
        increase_font_action.setShortcut("Ctrl++")
        increase_font_action.triggered.connect(self.increase_font_size)
        view_menu.addAction(increase_font_action)

        decrease_font_action = QAction("Decrease Font Size", self)
        decrease_font_action.setShortcut("Ctrl+-")
        decrease_font_action.triggered.connect(self.decrease_font_size)
        view_menu.addAction(decrease_font_action)

        reset_font_action = QAction("Reset Font Size", self)
        reset_font_action.setShortcut("Ctrl+0")
        reset_font_action.triggered.connect(self.reset_font_size)
        view_menu.addAction(reset_font_action)

        view_menu.addAction(self.preview_action)

    def create_new_note(self):
        if self.current_folder is None:
            QMessageBox.information(
                self,
                "No Folder Open",
                "Open a folder before creating a new note.",
            )
            return

        name, ok = QInputDialog.getText(
            self,
            "New Note",
            "Note name:",
        )

        if not ok or not name.strip():
            return

        name = name.strip()

        if not name.lower().endswith(".md"):
            name += ".md"

        target_folder = self.get_selected_folder()
        path = target_folder / name

        if path.exists():
            QMessageBox.warning(
                self,
                "File Exists",
                "A file with that name already exists.",
            )
            return

        try:
            path.write_text("", encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not create file:\n{error}",
            )
            return

        self.load_markdown_files()

    def create_new_folder(self):
        if self.current_folder is None:
            QMessageBox.information(
                self,
                "No Folder Open",
                "Open a folder before creating a new folder.",
            )
            return

        name, ok = QInputDialog.getText(
            self,
            "New Folder",
            "Folder name:",
        )

        if not ok or not name.strip():
            return

        target_folder = self.get_selected_folder()
        path = target_folder / name.strip()

        if path.exists():
            QMessageBox.warning(
                self,
                "Folder Exists",
                "A folder with that name already exists.",
            )
            return

        try:
            path.mkdir()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not create folder:\n{error}",
            )
            return

        self.load_markdown_files()

    def get_selected_folder(self):
        selected_items = self.file_tree.selectedItems()

        if not selected_items:
            return self.current_folder

        item = selected_items[0]
        path_data = item.data(0, Qt.UserRole)

        if path_data is None:
            return self.current_folder

        path = Path(path_data)

        if path.is_file():
            return path.parent

        return path

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
        self.file_tree.clear()

        if self.current_folder is None:
            return

        root_item = QTreeWidgetItem(
            self.file_tree,
            [self.current_folder.name],
        )

        root_item.setData(
            0,
            Qt.UserRole,
            str(self.current_folder),
        )

        root_item.setExpanded(True)

        self.add_folder_to_tree(
            self.current_folder,
            root_item,
        )

        root_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_DirIcon
        )
        root_item.setIcon(0, root_icon)
        self.file_tree.expandAll()

    def add_folder_to_tree(self, folder, parent_item):
        entries = sorted(
            folder.iterdir(),
            key=lambda path: (
                not path.is_dir(),
                path.name.lower(),
            ),
        )

        for path in entries:
            if path.is_dir():
                folder_item = QTreeWidgetItem(
                    parent_item,
                    [path.name],
                )

                folder_icon = self.style().standardIcon(
                    QStyle.StandardPixmap.SP_DirIcon
                )
                folder_item.setIcon(0, folder_icon)

                folder_item.setData(
                    0,
                    Qt.UserRole,
                    str(path),
                )

                self.add_folder_to_tree(
                    path,
                    folder_item,
                )

            elif path.suffix.lower() == ".md":
                file_item = QTreeWidgetItem(
                    parent_item,
                    [path.name],
                )

                file_icon = self.style().standardIcon(
                    QStyle.StandardPixmap.SP_FileIcon
                )
                file_item.setIcon(0, file_icon)

                file_item.setData(
                    0,
                    Qt.UserRole,
                    str(path),
                )

    def open_file_from_sidebar(self, item):
        path_data = item.data(0, Qt.UserRole)

        if path_data is None:
            return

        path = Path(path_data)

        if path.is_dir():
            return

        if not self.confirm_unsaved_changes():
            return

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