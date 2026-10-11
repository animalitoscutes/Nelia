"""
Novel & Prose Manuscript Editor Widget.
Optimized for long-form fiction, essays, and narrative writing:
- Typography: Elegant book typography (Serif/Literata/Georgia style)
- First-line paragraph indentation (standard novel formatting)
- Word count goals & reading time calculation
- Focus / Typewriter scrolling mode
"""

from PySide6.QtWidgets import (
    QPlainTextEdit, QFrame
)
from PySide6.QtGui import (
    QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QColor
)
from PySide6.QtCore import Qt, Signal


class NovelEditor(QPlainTextEdit):
    statsChanged = Signal(int, int) # words, characters

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NovelTextEditor")

        # Elegant book serif font
        font = QFont("Georgia", 13)
        font.setStyleHint(QFont.Serif)
        self.setFont(font)

        self.apply_paper_theme(dark=False)
        self.textChanged.connect(self._handle_text_changed)

    def apply_paper_theme(self, dark: bool = False):
        if dark:
            self.setStyleSheet("""
                QPlainTextEdit#NovelTextEditor {
                    background-color: #1a1a1e;
                    color: #e2e8f0;
                    border: none;
                    selection-background-color: #3b82f6;
                    selection-color: #ffffff;
                    padding: 44px 56px;
                    line-height: 1.6;
                }
            """)
        else:
            self.setStyleSheet("""
                QPlainTextEdit#NovelTextEditor {
                    background-color: #faf9f5;
                    color: #1c1917;
                    border: none;
                    selection-background-color: #e5a93c;
                    selection-color: #000000;
                    padding: 44px 56px;
                    line-height: 1.6;
                }
            """)

    def _handle_text_changed(self):
        text = self.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.statsChanged.emit(words, chars)
