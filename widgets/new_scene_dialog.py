"""
Dialog to create custom scenes ("Añadir escenas a mi gusto").
Features:
- Visual Slugline Builder (INT./EXT. buttons + Location autocomplete + Time of Day)
- Placement selection (Act assignment, insert after current scene)
- Initial dramatic setup (Synopsis, Character Goal, Obstacle, Cast)
- Real-time Courier Prime preview
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTextEdit, QRadioButton, QButtonGroup,
    QCompleter, QFrame, QCheckBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import QFont

from db.database import SessionLocal
from db.crud import (
    get_project_acts_and_scenes, get_known_locations, create_new_scene
)


class NewSceneDialog(QDialog):
    def __init__(self, project_id: int, current_scene_id: int = None, default_act_id: int = None, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.current_scene_id = current_scene_id
        self.default_act_id = default_act_id
        self.created_scene_id = None

        self.setWindowTitle("Añadir Nueva Escena a tu Gusto")
        self.resize(650, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #141417;
                color: #e4e4e7;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title
        lbl_head = QLabel("🎬 CREADOR DE ESCENA PERSONALIZADA")
        lbl_head.setStyleSheet("color: #e5a93c; font-size: 13px; font-weight: 700; letter-spacing: 0.8px;")
        layout.addWidget(lbl_head)

        # 1. Slugline Builder Box
        box_slug = QFrame()
        box_slug.setStyleSheet("background-color: #1a1a1f; border: 1px solid #2d2d38; border-radius: 6px; padding: 12px;")
        lay_slug = QVBoxLayout(box_slug)
        lay_slug.setSpacing(10)

        lay_slug.addWidget(QLabel("1. CONFIGURACIÓN DEL ENCABEZADO (SLUGLINE):"))

        # Type buttons (INT, EXT, etc.)
        row_type = QHBoxLayout()
        row_type.addWidget(QLabel("Tipo:"))
        self.btn_type_group = QButtonGroup(self)
        
        self.r_int = QPushButton("INT.")
        self.r_int.setCheckable(True)
        self.r_int.setChecked(True)
        self.r_int.setProperty("class", "mode-pill")
        self.btn_type_group.addButton(self.r_int, 0)
        row_type.addWidget(self.r_int)

        self.r_ext = QPushButton("EXT.")
        self.r_ext.setCheckable(True)
        self.r_ext.setProperty("class", "mode-pill")
        self.btn_type_group.addButton(self.r_ext, 1)
        row_type.addWidget(self.r_ext)

        self.r_intext = QPushButton("INT./EXT.")
        self.r_intext.setCheckable(True)
        self.r_intext.setProperty("class", "mode-pill")
        self.btn_type_group.addButton(self.r_intext, 2)
        row_type.addWidget(self.r_intext)

        row_type.addStretch()
        lay_slug.addLayout(row_type)

        # Location with autocomplete
        row_loc = QHBoxLayout()
        row_loc.addWidget(QLabel("Lugar / Set:"))
        self.edit_loc = QLineEdit()
        self.edit_loc.setPlaceholderText("Ej: LABORATORIO SUBTERRÁNEO, CAFETERÍA, AZOTEA...")
        self.edit_loc.setProperty("class", "inspector-field")
        self.edit_loc.textChanged.connect(self._update_preview)
        row_loc.addWidget(self.edit_loc)
        lay_slug.addLayout(row_loc)

        # Time of day
        row_time = QHBoxLayout()
        row_time.addWidget(QLabel("Momento:"))
        self.combo_time = QComboBox()
        self.combo_time.addItems([
            "NOCHE", "DÍA", "AMANECER", "ATARDECER",
            "CONTINUO", "MOMENTOS DESPUÉS", "MISMO TIEMPO", "FLASHBACK"
        ])
        self.combo_time.currentTextChanged.connect(self._update_preview)
        row_time.addWidget(self.combo_time)
        row_time.addStretch()
        lay_slug.addLayout(row_time)

        # Slugline Preview Card (Authentic Courier Preview)
        lay_slug.addWidget(QLabel("Vista previa en formato Hollywood estándar:"))
        self.lbl_preview = QLabel("INT. NUEVA ESCENA - NOCHE")
        self.lbl_preview.setStyleSheet("""
            background-color: #faf9f5;
            color: #09090b;
            font-family: 'Courier Prime', Courier, monospace;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 12px;
            border-radius: 4px;
        """)
        lay_slug.addWidget(self.lbl_preview)

        layout.addWidget(box_slug)

        # 2. Location in Project Structure (Act & Insertion position)
        box_pos = QFrame()
        box_pos.setStyleSheet("background-color: #1a1a1f; border: 1px solid #2d2d38; border-radius: 6px; padding: 12px;")
        lay_pos = QVBoxLayout(box_pos)
        lay_pos.setSpacing(8)

        lay_pos.addWidget(QLabel("2. UBICACIÓN DENTRO DEL GUION:"))
        
        row_act = QHBoxLayout()
        row_act.addWidget(QLabel("Acto / Bloque:"))
        self.combo_act = QComboBox()
        row_act.addWidget(self.combo_act)
        lay_pos.addLayout(row_act)

        self.chk_insert_after = QCheckBox("Insertar inmediatamente después de la escena activa")
        self.chk_insert_after.setChecked(True if current_scene_id else False)
        lay_pos.addWidget(self.chk_insert_after)

        layout.addWidget(box_pos)

        # 3. Initial Dramatic Setup
        box_drama = QFrame()
        box_drama.setStyleSheet("background-color: #1a1a1f; border: 1px solid #2d2d38; border-radius: 6px; padding: 12px;")
        lay_drama = QVBoxLayout(box_drama)
        lay_drama.setSpacing(8)

        lay_drama.addWidget(QLabel("3. PLANTEAMIENTO DRAMÁTICO (OPCIONAL):"))

        self.edit_synopsis = QLineEdit()
        self.edit_synopsis.setPlaceholderText("Sinopsis rápida: ¿Qué ocurre aquí?")
        self.edit_synopsis.setProperty("class", "inspector-field")
        lay_drama.addWidget(self.edit_synopsis)

        self.edit_goal = QLineEdit()
        self.edit_goal.setPlaceholderText("Objetivo del personaje: ¿Qué busca conseguir?")
        self.edit_goal.setProperty("class", "inspector-field")
        lay_drama.addWidget(self.edit_goal)

        layout.addWidget(box_drama)

        # Buttons (Accept / Cancel)
        row_btns = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "btn-subtle")
        self.btn_cancel.clicked.connect(self.reject)
        row_btns.addWidget(self.btn_cancel)

        row_btns.addStretch()

        self.btn_create = QPushButton("🎬 Crear Escena y Comenzar a Escribir")
        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #e5a93c;
                color: #09090b;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f59e0b;
            }
        """)
        self.btn_create.clicked.connect(self._create_scene)
        row_btns.addWidget(self.btn_create)

        layout.addLayout(row_btns)

        # Connect button group for slugline type
        self.btn_type_group.idClicked.connect(self._update_preview)

        # Load database data (acts, known locations, characters)
        self._load_db_options()
        self._update_preview()

    def _load_db_options(self):
        db = SessionLocal()
        try:
            acts, _, _, _ = get_project_acts_and_scenes(db, self.project_id)
            for act in acts:
                self.combo_act.addItem(f"📁 {act.title}", act.id)
            self.combo_act.addItem("📄 Escenas Sueltas / Sin Acto", None)

            if self.default_act_id:
                idx = self.combo_act.findData(self.default_act_id)
                if idx >= 0:
                    self.combo_act.setCurrentIndex(idx)

            # Location completer
            known_locs = get_known_locations(db, self.project_id)
            if known_locs:
                completer = QCompleter(known_locs, self)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.edit_loc.setCompleter(completer)
        finally:
            db.close()

    def _get_selected_type(self) -> str:
        cid = self.btn_type_group.checkedId()
        if cid == 1:
            return "EXT."
        elif cid == 2:
            return "INT./EXT."
        return "INT."

    def _update_preview(self):
        stype = self._get_selected_type()
        loc = self.edit_loc.text().strip().upper()
        if not loc:
            loc = "LUGAR / SET"
        t = self.combo_time.currentText()
        slug = f"{stype} {loc} - {t}"
        self.lbl_preview.setText(slug)

    def _create_scene(self):
        stype = self._get_selected_type()
        loc = self.edit_loc.text().strip().upper()
        if not loc:
            loc = "NUEVA LOCALIZACIÓN"
        t = self.combo_time.currentText()
        final_slug = f"{stype} {loc} - {t}"

        act_id = self.combo_act.currentData()
        insert_after = self.current_scene_id if self.chk_insert_after.isChecked() else None

        synopsis = self.edit_synopsis.text().strip()
        goal = self.edit_goal.text().strip()

        db = SessionLocal()
        try:
            sc = create_new_scene(
                db=db,
                project_id=self.project_id,
                act_id=act_id,
                title=final_slug,
                synopsis=synopsis,
                character_goal=goal,
                time_of_day=t,
                location=loc,
                insert_after_scene_id=insert_after
            )
            self.created_scene_id = sc.id
            self.accept()
        finally:
            db.close()
