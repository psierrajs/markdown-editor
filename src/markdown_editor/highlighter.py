import re

from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
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
        for pattern, text_format in self.rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - match.start()

                self.setFormat(
                    start,
                    length,
                    text_format,
                )