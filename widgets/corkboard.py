"""
The Beat Board / Corkboard (Pizarra de Tarjetas Index).
Loads live scenes and structural beats from PostgreSQL.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from db.database import SessionLocal
from db.crud import get_project_acts_and_scenes


class IndexCardWidget(QFrame):
    clicked = Signal(int) # Emits scene_id

    def __init__(self, scene_id: int, scene_no: int, title: str, synopsis: str, time_info: str, status: str = "", parent=None):
        super().__init__(parent)
        self.scene_id = scene_id
        self.setObjectName("IndexCard")

        # Color según estado
        status_color = "#3b82f6"
        if "Revisión" in status or "Azules" in status:
            status_color = "#e5a93c"
        elif "Aprobado" in status or "Rodaje" in status:
            status_color = "#10b981"
        elif "Descartado" in status:
            status_color = "#ef4444"

        self.setStyleSheet(f"""
            QFrame#IndexCard {{
                background-color: #1a1a1f;
                border: 1px solid #2f2f38;
                border-top: 4px solid {status_color};
                border-radius: 6px;
                padding: 10px;
                min-width: 220px;
                max-width: 260px;
            }}
            QFrame#IndexCard:hover {{
                border-color: #e5a93c;
                background-color: #212128;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header: Scene Number + Time
        top_row = QHBoxLayout()
        lbl_num = QLabel(f"ESCENA {scene_no}")
        lbl_num.setStyleSheet("color: #e5a93c; font-weight: 700; font-size: 11px;")
        lbl_time = QLabel(time_info or "NOCHE")
        lbl_time.setStyleSheet("color: #71717a; font-size: 10px;")
        top_row.addWidget(lbl_num)
        top_row.addStretch()
        top_row.addWidget(lbl_time)
        layout.addLayout(top_row)

        # Scene Title
        lbl_title = QLabel(title)
        lbl_title.setWordWrap(True)
        lbl_title.setStyleSheet("color: #f4f4f5; font-weight: 600; font-size: 12px;")
        layout.addWidget(lbl_title)

        # Synopsis
        lbl_synopsis = QLabel(synopsis or "(Sin sinopsis definida en el inspector)")
        lbl_synopsis.setWordWrap(True)
        lbl_synopsis.setStyleSheet("color: #a1a1aa; font-size: 11px; line-height: 1.3;")
        layout.addWidget(lbl_synopsis)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.scene_id)
        super().mousePressEvent(event)


class CorkboardWidget(QScrollArea):
    cardSelected = Signal(int)   # Emits scene_id
    sceneCreated = Signal(int)   # Emits scene_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project_id = None
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: #101012; border: none;")

        self.container = QWidget()
        self.main_layout = QHBoxLayout(self.container)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setWidget(self.container)

    def _open_new_scene_dialog(self, act_id: int = None):
        if not self.current_project_id:
            return
        from widgets.new_scene_dialog import NewSceneDialog
        dlg = NewSceneDialog(self.current_project_id, default_act_id=act_id, parent=self)
        if dlg.exec():
            if dlg.created_scene_id:
                self.populate_from_db(self.current_project_id)
                self.sceneCreated.emit(dlg.created_scene_id)

    def populate_from_db(self, project_id: int):
        self.current_project_id = project_id
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        db = SessionLocal()
        try:
            acts, standalone_scenes, _, _ = get_project_acts_and_scenes(db, project_id)

            for act in acts:
                self._add_act_column(act.title, act.scenes, act.id)

            if standalone_scenes:
                self._add_act_column("ESCENAS SIN ASIGNAR", standalone_scenes, None)
        finally:
            db.close()

    def _add_act_column(self, title: str, scenes, act_id: int = None):
        col_widget = QWidget()
        col_layout = QVBoxLayout(col_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(12)
        col_layout.setAlignment(Qt.AlignTop)

        header_row = QHBoxLayout()
        col_header = QLabel(title)
        col_header.setStyleSheet("""
            color: #d4d4d8;
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding-bottom: 6px;
        """)
        header_row.addWidget(col_header)
        header_row.addStretch()

        btn_add = QPushButton("+")
        btn_add.setFixedSize(22, 22)
        btn_add.setToolTip(f"Añadir escena a {title}")
        btn_add.setProperty("class", "btn-subtle")
        btn_add.clicked.connect(lambda: self._open_new_scene_dialog(act_id))
        header_row.addWidget(btn_add)
        col_layout.addLayout(header_row)

        for sc in scenes:
            card = IndexCardWidget(
                scene_id=sc.id,
                scene_no=sc.scene_number,
                title=sc.title,
                synopsis=sc.synopsis,
                time_info=sc.time_of_day,
                status=sc.revision_status
            )
            card.clicked.connect(self.cardSelected.emit)
            col_layout.addWidget(card)

        col_layout.addStretch()
        self.main_layout.addWidget(col_widget)
