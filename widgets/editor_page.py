"""
Physical Page Canvas Container.
Renders an authentic, centered writing sheet with realistic paper boundaries,
subtle drop shadow, and zoom capabilities. Avoids full-window stretched text.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from widgets.screenplay_editor import ScreenplayEditor


class PageCanvasContainer(QScrollArea):
    """
    Scrollable desktop canvas holding the physical page in the center,
    matching Final Draft / Scrivener page layout ergonomics.
    """
    def __init__(self, editor: ScreenplayEditor, parent=None):
        super().__init__(parent)
        self.setObjectName("PageCanvasScroll")
        self.editor = editor

        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)

        # Surrounding canvas widget
        self.surround = QWidget()
        self.surround.setObjectName("PageCanvasSurround")
        surround_layout = QVBoxLayout(self.surround)
        surround_layout.setContentsMargins(40, 30, 40, 50)
        surround_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        # The Physical Page Card
        self.page_card = QFrame()
        self.page_card.setObjectName("ScreenplayPaperCard")
        # Standard US Letter proportions (approx 816 x 1056 px at standard DPI)
        self.page_card.setMinimumWidth(750)
        self.page_card.setMaximumWidth(850)
        self.page_card.setMinimumHeight(1050)

        # Subtle paper depth shadow (crafting human software look, not flat AI template)
        shadow = QGraphicsDropShadowEffect(self.page_card)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 8)
        self.page_card.setGraphicsEffect(shadow)

        # Card layout embedding the editor
        card_layout = QVBoxLayout(self.page_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(self.editor)

        surround_layout.addWidget(self.page_card)
        self.setWidget(self.surround)

    def set_dark_mode(self, dark: bool):
        if dark:
            self.page_card.setObjectName("ScreenplayPaperCardDark")
            self.editor.apply_paper_theme(dark=True)
        else:
            self.page_card.setObjectName("ScreenplayPaperCard")
            self.editor.apply_paper_theme(dark=False)
        self.page_card.style().unpolish(self.page_card)
        self.page_card.style().polish(self.page_card)
