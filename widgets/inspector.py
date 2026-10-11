"""
The Inspector Panel (Right Sidebar).
Directly bound to PostgreSQL database records for scenes:
- Synopsis / Dramatic Beat
- Character Goal & Dramatic Need
- Conflict / Obstacle / Twist
- Revision Status, Lighting/Time, Location, Cast, and Notes
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QWidget, QLineEdit, QTextEdit, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer


class InspectorWidget(QFrame):
    metadataChanged = Signal(dict) # Emits changed fields to save into PostgreSQL

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InspectorPanel")
        self.setProperty("class", "panel-inspector")
        self.current_scene_id = None
        self._block_save = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Header Title
        self.lbl_title = QLabel("INSPECTOR DE ESCENA")
        self.lbl_title.setProperty("class", "panel-header-title")
        layout.addWidget(self.lbl_title)

        from widgets.continuity_tab import ContinuityTabWidget
        self.continuity_tab = ContinuityTabWidget()

        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_scene_tab(), "Sinopsis")
        tabs.addTab(self.continuity_tab, "Auditor IA")
        tabs.addTab(self._create_metadata_tab(), "Metadatos")
        tabs.addTab(self._create_goals_tab(), "Metas")
        tabs.addTab(self._create_notes_tab(), "Notas")
        layout.addWidget(tabs)

        # Debounce timer for saving to database
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._emit_changes)

    def _create_scene_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(8)

        lbl_synopsis = QLabel("SINOPSIS / BEAT DRAMÁTICO:")
        lbl_synopsis.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lay.addWidget(lbl_synopsis)

        self.synopsis_edit = QTextEdit()
        self.synopsis_edit.setProperty("class", "inspector-field")
        self.synopsis_edit.setPlaceholderText("Describe qué ocurre y cómo cambia el estado de la historia...")
        self.synopsis_edit.setMaximumHeight(130)
        self.synopsis_edit.textChanged.connect(self._trigger_save)
        lay.addWidget(self.synopsis_edit)

        lbl_goal = QLabel("OBJETIVO DEL PERSONAJE:")
        lbl_goal.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lay.addWidget(lbl_goal)

        self.goal_edit = QLineEdit()
        self.goal_edit.setProperty("class", "inspector-field")
        self.goal_edit.setPlaceholderText("¿Qué desea desesperadamente?")
        self.goal_edit.textChanged.connect(self._trigger_save)
        lay.addWidget(self.goal_edit)

        lbl_conflict = QLabel("OBSTÁCULO / GIRO:")
        lbl_conflict.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lay.addWidget(lbl_conflict)

        self.conflict_edit = QLineEdit()
        self.conflict_edit.setProperty("class", "inspector-field")
        self.conflict_edit.setPlaceholderText("¿Qué le impide conseguirlo?")
        self.conflict_edit.textChanged.connect(self._trigger_save)
        lay.addWidget(self.conflict_edit)

        lay.addStretch()
        return w

    def _create_metadata_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(10)

        # Estado de revisión
        lay.addWidget(QLabel("ESTADO DE REVISIÓN:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["⚪ Primer Borrador", "🟡 En Revisión (Páginas Azules)", "🟢 Aprobado para Rodaje", "🔴 Descartado"])
        self.status_combo.currentTextChanged.connect(self._trigger_save)
        lay.addWidget(self.status_combo)

        # Momento
        lay.addWidget(QLabel("MOMENTO / ILUMINACIÓN:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["NOCHE", "DÍA", "AMANECER", "ATARDECER", "CONTINUO", "MAGIA HORA (GOLDEN HOUR)"])
        self.time_combo.currentTextChanged.connect(self._trigger_save)
        lay.addWidget(self.time_combo)

        # Localización
        lay.addWidget(QLabel("LOCALIZACIÓN / SET:"))
        self.loc_edit = QLineEdit()
        self.loc_edit.setProperty("class", "inspector-field")
        self.loc_edit.setPlaceholderText("Ej: Laboratorio Subterráneo Nivel -2")
        self.loc_edit.textChanged.connect(self._trigger_save)
        lay.addWidget(self.loc_edit)

        # Personajes presentes
        lay.addWidget(QLabel("PERSONAJES EN ESCENA:"))
        self.cast_edit = QTextEdit()
        self.cast_edit.setProperty("class", "inspector-field")
        self.cast_edit.setPlaceholderText("Julián, Dra. Elena, Guardias...")
        self.cast_edit.setMaximumHeight(80)
        self.cast_edit.textChanged.connect(self._trigger_save)
        lay.addWidget(self.cast_edit)

        lay.addStretch()
        return w

    def _create_goals_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(10)

        lbl = QLabel("OBJETIVO DE ESCRITURA DIARIA:")
        lbl.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lay.addWidget(lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1500)
        self.progress_bar.setValue(350)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1c1c20;
                border: 1px solid #2e2e33;
                border-radius: 4px;
                text-align: center;
                color: #f4f4f5;
                font-weight: 600;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #e5a93c;
                border-radius: 3px;
            }
        """)
        lay.addWidget(self.progress_bar)

        self.lbl_progress_text = QLabel("350 / 1500 palabras hoy")
        self.lbl_progress_text.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        lay.addWidget(self.lbl_progress_text)

        lay.addWidget(QLabel("ESTÁNDAR CINEMATOGRÁFICO:"))
        pacing_card = QFrame()
        pacing_card.setStyleSheet("background-color: #1a1a1e; border: 1px solid #2b2b30; border-radius: 6px; padding: 10px;")
        pacing_lay = QVBoxLayout(pacing_card)
        pacing_lay.addWidget(QLabel("⏱️ Regla: 1 página de guion = ~1 minuto"))
        pacing_lay.addWidget(QLabel("📄 Tipografía: Courier Prime 12pt"))
        lay.addWidget(pacing_card)

        lay.addStretch()
        return w

    def _create_notes_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(8)

        lbl = QLabel("NOTAS AL MARGEN / SCRATCHPAD:")
        lbl.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        lay.addWidget(lbl)

        self.notes_edit = QTextEdit()
        self.notes_edit.setProperty("class", "inspector-field")
        self.notes_edit.setPlaceholderText("Anotaciones privadas guardadas en PostgreSQL...")
        self.notes_edit.textChanged.connect(self._trigger_save)
        lay.addWidget(self.notes_edit)
        return w

    def load_scene_data(self, scene):
        """Carga datos reales desde la base de datos PostgreSQL."""
        self._block_save = True
        self.current_scene_id = scene.id
        self.lbl_title.setText(f"INSPECTOR: ESCENA {scene.scene_number}")

        self.synopsis_edit.setPlainText(scene.synopsis or "")
        self.goal_edit.setText(scene.character_goal or "")
        self.conflict_edit.setText(scene.conflict_obstacle or "")

        idx_status = self.status_combo.findText(scene.revision_status or "")
        if idx_status >= 0:
            self.status_combo.setCurrentIndex(idx_status)

        idx_time = self.time_combo.findText(scene.time_of_day or "")
        if idx_time >= 0:
            self.time_combo.setCurrentIndex(idx_time)

        self.loc_edit.setText(scene.location or "")
        self.cast_edit.setPlainText(scene.cast_members or "")
        self.notes_edit.setPlainText(scene.notes or "")

        self._block_save = False

    def _trigger_save(self):
        if not self._block_save and self.current_scene_id:
            self.save_timer.start(500) # Debounce 500ms

    def _emit_changes(self):
        if not self.current_scene_id:
            return
        data = {
            "scene_id": self.current_scene_id,
            "synopsis": self.synopsis_edit.toPlainText().strip(),
            "character_goal": self.goal_edit.text().strip(),
            "conflict_obstacle": self.conflict_edit.text().strip(),
            "revision_status": self.status_combo.currentText(),
            "time_of_day": self.time_combo.currentText(),
            "location": self.loc_edit.text().strip(),
            "cast_members": self.cast_edit.toPlainText().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }
        self.metadataChanged.emit(data)
