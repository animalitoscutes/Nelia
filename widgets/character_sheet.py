"""
Character Dossier & Psychology Sheet Widget.
Allows the author to view, edit, and create rich characters with:
- Role, Bio & Backstory
- Dramatic Need (Want vs Need)
- Fatal Flaw & Psychological Wound
- Dialogue Voice & Speech Pattern
- Arc of Transformation
Directly saved into PostgreSQL and synced with AI Agents.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QScrollArea, QFrame,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from db.database import SessionLocal
from db.crud import get_character, update_character, delete_character


class CharacterSheetWidget(QScrollArea):
    characterSaved = Signal(int)
    characterDeleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_character_id = None
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: #121215; border: none;")

        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Main Card Frame
        card = QFrame()
        card.setMinimumWidth(680)
        card.setMaximumWidth(840)
        card.setStyleSheet("""
            QFrame {
                background-color: #18181d;
                border: 1px solid #282832;
                border-radius: 8px;
                padding: 24px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        # Header Title
        top_bar = QHBoxLayout()
        self.lbl_heading = QLabel("FICHA DE PERSONAJE & PSICOLOGÍA")
        self.lbl_heading.setStyleSheet("color: #e5a93c; font-size: 13px; font-weight: 700; letter-spacing: 0.8px;")
        top_bar.addWidget(self.lbl_heading)
        top_bar.addStretch()

        self.btn_delete = QPushButton("🗑️ Eliminar Personaje")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #450a0a;
                color: #f87171;
                border: 1px solid #7f1d1d;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                color: #ffffff;
            }
        """)
        self.btn_delete.clicked.connect(self._on_delete)
        top_bar.addWidget(self.btn_delete)
        card_layout.addLayout(top_bar)

        # Name and Role
        row_identity = QHBoxLayout()
        
        vbox_name = QVBoxLayout()
        vbox_name.addWidget(QLabel("NOMBRE DEL PERSONAJE:"))
        self.edit_name = QLineEdit()
        self.edit_name.setProperty("class", "inspector-field")
        self.edit_name.setPlaceholderText("Ej: Julián Valdés")
        vbox_name.addWidget(self.edit_name)
        row_identity.addLayout(vbox_name, 2)

        vbox_role = QVBoxLayout()
        vbox_role.addWidget(QLabel("ROL DRAMÁTICO:"))
        self.combo_role = QComboBox()
        self.combo_role.addItems([
            "Protagonista", "Antagonista", "Aliado / Coprotagonista",
            "Mentor", "Interés Amoroso", "Secundario Clave", "Antagonista Menor"
        ])
        vbox_role.addWidget(self.combo_role)
        row_identity.addLayout(vbox_role, 1)

        card_layout.addLayout(row_identity)

        # Bio and Backstory
        card_layout.addWidget(QLabel("BIOGRAFÍA Y TRASFONDO (BACKSTORY):"))
        self.edit_bio = QTextEdit()
        self.edit_bio.setProperty("class", "inspector-field")
        self.edit_bio.setPlaceholderText("Historia previa, profesión, trauma formativo, secretos no revelados...")
        self.edit_bio.setMaximumHeight(120)
        card_layout.addWidget(self.edit_bio)

        # Dramatic Need (Want vs Need)
        card_layout.addWidget(QLabel("MOTIVACIÓN / DESEO VS NECESIDAD DRAMÁTICA:"))
        self.edit_need = QLineEdit()
        self.edit_need.setProperty("class", "inspector-field")
        self.edit_need.setPlaceholderText("¿Qué persigue externamente (Want) y qué necesita sanar internamente (Need)?")
        card_layout.addWidget(self.edit_need)

        # Fatal Flaw / Wound
        card_layout.addWidget(QLabel("DEFECTO FATAL / HERIDA PSICOLÓGICA (FATAL FLAW):"))
        self.edit_flaw = QLineEdit()
        self.edit_flaw.setProperty("class", "inspector-field")
        self.edit_flaw.setPlaceholderText("Ej: Arrogancia intelectual, desconfianza crónica, culpa paralizante...")
        card_layout.addWidget(self.edit_flaw)

        # Dialogue Style / Voice
        card_layout.addWidget(QLabel("VOZ Y ESTILO DE DIÁLOGO (PATRÓN DE HABLA):"))
        self.edit_voice = QLineEdit()
        self.edit_voice.setProperty("class", "inspector-field")
        self.edit_voice.setPlaceholderText("¿Habla rápido? ¿Usa jerga técnica? ¿Sarcástico? ¿Frases cortas o elocuentes?")
        card_layout.addWidget(self.edit_voice)

        # Arc of Transformation
        card_layout.addWidget(QLabel("ARCO DE TRANSFORMACIÓN (INICIO VS DESENLACE):"))
        self.edit_arc = QTextEdit()
        self.edit_arc.setProperty("class", "inspector-field")
        self.edit_arc.setPlaceholderText("¿Cómo empieza al inicio de la obra y en qué persona se convierte al final?")
        self.edit_arc.setMaximumHeight(100)
        card_layout.addWidget(self.edit_arc)

        # Save Button
        self.btn_save = QPushButton("💾 Guardar Cambios en PostgreSQL")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #e5a93c;
                color: #09090b;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f59e0b;
            }
        """)
        self.btn_save.clicked.connect(self._save_changes)
        card_layout.addWidget(self.btn_save)

        layout.addWidget(card)
        self.setWidget(self.container)

    def load_character(self, character_id: int):
        self.current_character_id = character_id
        db = SessionLocal()
        try:
            char = get_character(db, character_id)
            if not char:
                return

            self.lbl_heading.setText(f"FICHA DE PERSONAJE: {char.name.upper()}")
            self.edit_name.setText(char.name or "")
            
            idx = self.combo_role.findText(char.role or "Protagonista")
            if idx >= 0:
                self.combo_role.setCurrentIndex(idx)
            else:
                self.combo_role.setEditText(char.role or "")

            self.edit_bio.setPlainText(char.bio or "")
            self.edit_need.setText(char.dramatic_need or "")
            self.edit_flaw.setText(char.fatal_flaw or "")
            self.edit_voice.setText(char.dialogue_style or "")
            self.edit_arc.setPlainText(char.arc or "")
        finally:
            db.close()

    def _save_changes(self):
        if not self.current_character_id:
            return

        db = SessionLocal()
        try:
            update_character(
                db,
                self.current_character_id,
                name=self.edit_name.text().strip(),
                role=self.combo_role.currentText(),
                bio=self.edit_bio.toPlainText().strip(),
                dramatic_need=self.edit_need.text().strip(),
                fatal_flaw=self.edit_flaw.text().strip(),
                dialogue_style=self.edit_voice.text().strip(),
                arc=self.edit_arc.toPlainText().strip()
            )
            QMessageBox.information(self, "Guardado", "Ficha de personaje actualizada con éxito en PostgreSQL.")
            self.characterSaved.emit(self.current_character_id)
        finally:
            db.close()

    def _on_delete(self):
        if not self.current_character_id:
            return
        ans = QMessageBox.question(
            self,
            "Eliminar Personaje",
            f"¿Estás seguro de que deseas eliminar permanentemente a '{self.edit_name.text()}' de PostgreSQL?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            char_id = self.current_character_id
            db = SessionLocal()
            try:
                delete_character(db, char_id)
            finally:
                db.close()
            self.characterDeleted.emit(char_id)
