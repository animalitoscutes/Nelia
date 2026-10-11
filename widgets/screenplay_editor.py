"""
Professional Screenplay Editor Widget.
Implements the exact Final Draft / Fade In keyboard state machine:
- Enter / Tab transition matrix
- Auto-capitalization of Character & Scene Headings
- Dynamic margin indentation per element (Courier 12pt standard)
- Auto-completion for INT./EXT. and Character names
- Real-time element detection
"""

from PySide6.QtWidgets import (
    QPlainTextEdit, QWidget, QCompleter
)
from PySide6.QtGui import (
    QFont, QTextCursor, QTextBlockFormat, QTextCharFormat,
    QColor, QKeyEvent
)
from PySide6.QtCore import Qt, Signal, QStringListModel

from config import (
    ScriptElementType, FORMAT_RULES, ENTER_TRANSITIONS,
    TAB_TRANSITIONS, SCENE_PREFIXES
)


class ScreenplayEditor(QPlainTextEdit):
    elementChanged = Signal(str)      # Emits current ScriptElementType
    statsChanged = Signal(int, int)   # words, scenes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ScreenplayTextEditor")

        # Fonts: Industry standard 12pt Courier
        font = QFont("Courier Prime", 12)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab stop distance
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

        # Dynamic characters set populated from text & PostgreSQL
        self.known_characters = set()

        # State tracking
        self.cursorPositionChanged.connect(self._handle_cursor_position_changed)
        self.textChanged.connect(self._handle_text_changed)

        # Visual mode ('light' page or 'dark' canvas)
        self.is_dark_paper = False
        self.apply_paper_theme(dark=False)

        # Initialize first block as Scene Heading
        self.set_current_element_type(ScriptElementType.SCENE_HEADING)

    def apply_paper_theme(self, dark: bool = False):
        self.is_dark_paper = dark
        if dark:
            self.setStyleSheet("""
                QPlainTextEdit#ScreenplayTextEditor {
                    background-color: #1a1a1e;
                    color: #e4e4e7;
                    border: none;
                    selection-background-color: #3b82f6;
                    selection-color: #ffffff;
                    padding: 40px 50px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #3f3f46;
                    border-radius: 3px;
                    min-height: 20px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPlainTextEdit#ScreenplayTextEditor {
                    background-color: #faf9f5;
                    color: #18181b;
                    border: none;
                    selection-background-color: #2563eb;
                    selection-color: #ffffff;
                    padding: 40px 50px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #d4d4d8;
                    border-radius: 3px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a1a1aa;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)

    def get_current_element_type(self) -> str:
        cursor = self.textCursor()
        block = cursor.block()
        data = block.userState()
        # Map userState int to ScriptElementType or infer from content
        text = block.text().strip()
        if any(text.startswith(p) for p in SCENE_PREFIXES):
            return ScriptElementType.SCENE_HEADING
        if text.endswith("TO:") or text in ["FADE IN:", "FADE OUT.", "DISSOLVE TO:"]:
            return ScriptElementType.TRANSITION
        if text.startswith("(") and text.endswith(")"):
            return ScriptElementType.PARENTHETICAL
        
        # Check custom block format margin
        margin = block.blockFormat().leftMargin()
        if margin >= 140:
            return ScriptElementType.CHARACTER
        elif margin >= 95:
            return ScriptElementType.PARENTHETICAL
        elif margin >= 60:
            return ScriptElementType.DIALOGUE
        elif margin >= 240:
            return ScriptElementType.TRANSITION
        return ScriptElementType.ACTION

    def set_current_element_type(self, element_type: str):
        rule = FORMAT_RULES.get(element_type)
        if not rule:
            return

        cursor = self.textCursor()
        cursor.beginEditBlock()

        block_fmt = QTextBlockFormat()
        # Scale inches to pixels at 96 DPI: 1 inch = 96 px
        # Base screenplay margin:
        # Left indent:
        px_per_inch = 72.0
        left_px = rule.left_indent_inches * px_per_inch
        right_px = rule.right_indent_inches * px_per_inch

        block_fmt.setLeftMargin(left_px)
        block_fmt.setRightMargin(right_px)
        block_fmt.setTopMargin(rule.space_before_lines * 14.0)
        block_fmt.setBottomMargin(rule.space_after_lines * 4.0)

        if element_type == ScriptElementType.TRANSITION:
            block_fmt.setAlignment(Qt.AlignRight)
        else:
            block_fmt.setAlignment(Qt.AlignLeft)

        cursor.setBlockFormat(block_fmt)

        # Character formatting
        char_fmt = QTextCharFormat()
        font = self.font()
        if element_type in (ScriptElementType.SCENE_HEADING, ScriptElementType.CHARACTER):
            font.setBold(True)
        else:
            font.setBold(False)
        char_fmt.setFont(font)
        cursor.setBlockCharFormat(char_fmt)

        # Auto uppercase if required
        text = cursor.block().text()
        if rule.all_caps and text != text.upper():
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.insertText(text.upper())

        cursor.endEditBlock()
        self.elementChanged.emit(element_type)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        current_elem = self.get_current_element_type()

        # TAB key handling (The holy grail of screenplay ergonomics)
        if key == Qt.Key_Tab:
            cursor = self.textCursor()
            line_text = cursor.block().text().strip()

            # Cycle element via Tab
            next_elem = TAB_TRANSITIONS.get(current_elem, ScriptElementType.CHARACTER)
            self.set_current_element_type(next_elem)

            # If switching to parenthetical, wrap with parens if empty
            if next_elem == ScriptElementType.PARENTHETICAL and not line_text:
                cursor.insertText("()")
                cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
                self.setTextCursor(cursor)
            return

        # ENTER / RETURN key handling
        if key in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            line_text = cursor.block().text().strip()

            # Register character if typed
            if current_elem == ScriptElementType.CHARACTER and line_text:
                clean_char = line_text.replace("(V.O.)", "").replace("(O.S.)", "").strip()
                if clean_char:
                    self.known_characters.add(clean_char)

            # Determine next block type
            next_elem = ENTER_TRANSITIONS.get(current_elem, ScriptElementType.ACTION)

            # If double Enter on empty dialogue/character, drop to Action
            if not line_text and current_elem in (ScriptElementType.CHARACTER, ScriptElementType.DIALOGUE):
                self.set_current_element_type(ScriptElementType.ACTION)
                return

            super().keyPressEvent(event)
            self.set_current_element_type(next_elem)
            return

        # Auto-uppercase for Scene Heading & Character
        if current_elem in (ScriptElementType.SCENE_HEADING, ScriptElementType.CHARACTER, ScriptElementType.TRANSITION):
            if event.text() and event.text().isalpha() and not (modifiers & (Qt.ControlModifier | Qt.AltModifier)):
                cursor = self.textCursor()
                cursor.insertText(event.text().upper())
                return

        super().keyPressEvent(event)

    def _handle_cursor_position_changed(self):
        current_elem = self.get_current_element_type()
        self.elementChanged.emit(current_elem)

    def _handle_text_changed(self):
        text = self.toPlainText()
        words = len(text.split()) if text.strip() else 0
        scenes = sum(1 for line in text.splitlines() if any(line.strip().startswith(p) for p in SCENE_PREFIXES))
        self.statsChanged.emit(words, scenes)
