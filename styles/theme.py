"""
Theme and styling definitions for Scriptor Studio.
Clean, modern slate/zinc studio aesthetic inspired by DaVinci Resolve, Final Draft 13, and Ulysses.
Strictly no generic AI neon gradients.
"""

DARK_THEME_QSS = """
/* ====================================================================
   SCRIPTOR STUDIO - PROFESSIONAL WORKSPACE QSS
   Clean Zinc / Graphite Studio Aesthetics
   ==================================================================== */

QMainWindow, QWidget#MainContainer {
    background-color: #121214;
    color: #e4e4e7;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Ubuntu, sans-serif;
    font-size: 13px;
}

/* Toolbars & Headers */
QToolBar {
    background-color: #18181b;
    border-bottom: 1px solid #27272a;
    padding: 6px 10px;
    spacing: 8px;
}

QToolBar QLabel {
    color: #a1a1aa;
    font-weight: 500;
}

/* Segmented Mode Switcher Buttons */
QPushButton[class="mode-pill"] {
    background-color: #27272a;
    color: #a1a1aa;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton[class="mode-pill"]:hover {
    background-color: #3f3f46;
    color: #f4f4f5;
}

QPushButton[class="mode-pill"]:checked, QPushButton:checked {
    background-color: #e5a93c;
    color: #09090b;
    border: 1px solid #d99b26;
    font-weight: 700;
}

/* Primary Action Buttons */
QPushButton[class="btn-subtle"] {
    background-color: transparent;
    color: #d4d4d8;
    border: 1px solid #3f3f46;
    border-radius: 5px;
    padding: 5px 10px;
}

QPushButton[class="btn-subtle"]:hover {
    background-color: #27272a;
    border-color: #52525b;
}

QPushButton[class="btn-subtle"]:pressed {
    background-color: #18181b;
}

/* ComboBox Element Selector */
QComboBox {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    color: #f4f4f5;
    padding: 4px 12px;
    font-weight: 600;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #e5a93c;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #3f3f46;
}

QComboBox QAbstractItemView {
    background-color: #18181b;
    border: 1px solid #3f3f46;
    selection-background-color: #27272a;
    selection-color: #e5a93c;
    color: #e4e4e7;
    padding: 4px;
}

/* Splitters */
QSplitter::handle {
    background-color: #1c1c1f;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:horizontal:hover {
    background-color: #e5a93c;
}

/* Dock & Sidebar Panels (Binder / Inspector) */
QFrame[class="panel-sidebar"] {
    background-color: #151518;
    border-right: 1px solid #27272a;
}

QFrame[class="panel-inspector"] {
    background-color: #151518;
    border-left: 1px solid #27272a;
}

QLabel[class="panel-header-title"] {
    color: #71717a;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 10px 14px 6px 14px;
}

/* Tree & List Views (The Binder) */
QTreeView, QListView {
    background-color: transparent;
    border: none;
    color: #d4d4d8;
    outline: none;
    padding: 4px;
}

QTreeView::item {
    padding: 7px 8px;
    border-radius: 5px;
    margin-bottom: 2px;
}

QTreeView::item:hover {
    background-color: #202024;
    color: #ffffff;
}

QTreeView::item:selected {
    background-color: #27272e;
    color: #e5a93c;
    font-weight: 600;
}

/* Physical Page Canvas Surroundings */
QScrollArea#PageCanvasScroll {
    background-color: #101012;
    border: none;
}

QWidget#PageCanvasSurround {
    background-color: #101012;
}

/* Screenplay Paper Card */
QFrame#ScreenplayPaperCard {
    background-color: #faf9f6; /* Authentic Warm Off-White Script Paper */
    border: 1px solid #202024;
    border-radius: 4px;
}

QFrame#ScreenplayPaperCardDark {
    background-color: #1c1c20; /* Pro Night Writing Canvas */
    border: 1px solid #2d2d33;
    border-radius: 4px;
}

/* Status Bar */
QStatusBar {
    background-color: #141416;
    border-top: 1px solid #27272a;
    color: #a1a1aa;
    font-size: 12px;
    padding: 4px 10px;
}

QStatusBar QLabel {
    color: #a1a1aa;
    padding: 0 8px;
}

QStatusBar QLabel#StatsPill {
    background-color: #202024;
    border: 1px solid #2e2e33;
    border-radius: 10px;
    padding: 2px 10px;
    color: #e4e4e7;
    font-weight: 600;
}

/* Inspector Tabs and Fields */
QTabWidget::pane {
    border: none;
    background-color: transparent;
}

QTabBar::tab {
    background: transparent;
    color: #71717a;
    padding: 6px 9px;
    font-weight: 600;
    font-size: 11px;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #f4f4f5;
    border-bottom: 2px solid #e5a93c;
}

QTabBar::tab:hover {
    color: #d4d4d8;
}

QLineEdit, QTextEdit {
    background-color: #1c1c20;
    border: 1px solid #2e2e33;
    border-radius: 5px;
    color: #f4f4f5;
    padding: 6px 10px;
    font-size: 12px;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #e5a93c;
}

/* Beat Board Cards */
QFrame.beat-card {
    background-color: #1e1e24;
    border: 1px solid #2e2e35;
    border-top: 3px solid #e5a93c;
    border-radius: 6px;
    padding: 10px;
}

QFrame.beat-card:hover {
    border-color: #52525e;
    border-top: 3px solid #f59e0b;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #141416;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2e2e33;
    min-height: 24px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #52525b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
