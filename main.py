"""
SCRIPTOR STUDIO - Enterprise GUI Suite for Screenwriters and Novelists.
Integrated with PostgreSQL Database Persistence (Docker container scriptor_postgres)
and Local Multi-Agent AI Engine (openai-agents, Ollama, Qwen 2.5 7B, FastAPI).
Includes:
- Scene deletion (Delete button, context menu, Del/Backspace keys)
- Full Character Dossier & Psychology Editor (Want vs Need, Fatal Flaw, Voice, Arc)
"""

import sys
import os
import subprocess
import urllib.request
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStackedWidget, QToolBar, QComboBox, QPushButton,
    QLabel, QStatusBar, QFileDialog, QMessageBox, QSlider, QSizePolicy
)
from PySide6.QtGui import QIcon, QFont, QKeySequence, QAction, QShortcut, QTextCursor, QPixmap
from PySide6.QtCore import Qt, QSize, QTimer

from config import ScriptElementType, FORMAT_RULES
from styles.theme import DARK_THEME_QSS
from widgets.screenplay_editor import ScreenplayEditor
from widgets.novel_editor import NovelEditor
from widgets.editor_page import PageCanvasContainer
from widgets.binder import BinderWidget
from widgets.inspector import InspectorWidget
from widgets.corkboard import CorkboardWidget
from widgets.ai_chat_dock import AIChatDock
from widgets.character_sheet import CharacterSheetWidget
from ai.config import FASTAPI_HOST, FASTAPI_PORT

# PostgreSQL layer
from db.database import init_db, SessionLocal
from db.crud import (
    get_or_create_default_project, get_scene, update_scene_content,
    update_scene_metadata, get_project_acts_and_scenes
)


class ScriptorStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NELIA — Suite de Escritura & Guion | PostgreSQL")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon_256.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1540, 920)
        self.setMinimumSize(1024, 700)

        # 1. Initialize PostgreSQL database tables
        init_db()

        self.server_process = None
        self._ensure_ai_server_running()

        self.current_project_id = None
        self.current_scene_id = None
        self._is_loading_scene = False

        # 2. Main Central Stack and Splitter
        self._init_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()

        # 3. Connect signals & debouncers
        self._connect_signals()

        # 4. Load project and scenes dynamically from PostgreSQL
        self._load_initial_project_from_db()

    def _ensure_ai_server_running(self):
        """Verifica si el backend FastAPI en el puerto 8765 está activo; si no, lo inicia."""
        url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/status"
        is_running = False
        try:
            with urllib.request.urlopen(url, timeout=0.8) as resp:
                if resp.status == 200:
                    is_running = True
        except Exception:
            is_running = False

        if not is_running:
            try:
                cmd = [
                    sys.executable, "-m", "uvicorn", "ai.server:app",
                    "--host", FASTAPI_HOST,
                    "--port", str(FASTAPI_PORT),
                    "--log-level", "warning"
                ]
                self.server_process = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"[Aviso] No se pudo auto-iniciar el servidor FastAPI: {e}")

    def _init_ui(self):
        main_container = QWidget()
        main_container.setObjectName("MainContainer")
        self.setCentralWidget(main_container)

        root_layout = QVBoxLayout(main_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Primary Splitter (Binder | Canvas | Inspector | AI Chat Dock)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)

        # 1. Left: The Binder (Navigator)
        self.binder = BinderWidget()
        self.binder.setMinimumWidth(200)
        self.binder.setMaximumWidth(340)
        self.splitter.addWidget(self.binder)

        # 2. Center: Stacked Workspaces (Screenplay / Novel / Beat Board / Character Sheet)
        self.center_stack = QStackedWidget()

        # Workspace 0: Screenplay Canvas
        self.screenplay_editor = ScreenplayEditor()
        self.screenplay_page = PageCanvasContainer(self.screenplay_editor)
        self.center_stack.addWidget(self.screenplay_page)

        # Workspace 1: Novel / Manuscript Canvas
        self.novel_editor = NovelEditor()
        self.novel_page = PageCanvasContainer(self.novel_editor)
        self.center_stack.addWidget(self.novel_page)

        # Workspace 2: Beat Board / Corkboard
        self.corkboard = CorkboardWidget()
        self.center_stack.addWidget(self.corkboard)

        # Workspace 3: Character Dossier Sheet
        self.character_sheet = CharacterSheetWidget()
        self.center_stack.addWidget(self.character_sheet)

        self.splitter.addWidget(self.center_stack)

        # 3. Right 1: Inspector (with Continuity Auditor Tab)
        self.inspector = InspectorWidget()
        self.inspector.setMinimumWidth(280)
        self.inspector.setMaximumWidth(390)
        self.splitter.addWidget(self.inspector)

        # 4. Right 2: AI Co-Writer Chat Dock
        self.ai_dock = AIChatDock()
        self.ai_dock.setMinimumWidth(280)
        self.ai_dock.setMaximumWidth(420)
        self.splitter.addWidget(self.ai_dock)

        # Proportions: Binder (210) | Canvas (660) | Inspector (290) | AI Dock (320)
        self.splitter.setSizes([210, 660, 290, 320])
        root_layout.addWidget(self.splitter)

        # Context providers for AI agents
        self.ai_dock.set_context_provider(self._get_document_context)
        self.inspector.continuity_tab.set_context_provider(self._get_document_context)
        self.ai_dock.insertSnippetToDocument.connect(self._insert_snippet_to_active_editor)

    def _load_initial_project_from_db(self):
        """Carga el proyecto real de PostgreSQL sin nada hardcodeado."""
        db = SessionLocal()
        try:
            project = get_or_create_default_project(db)
            self.current_project_id = project.id
            self.setWindowTitle(f"Scriptor Studio — [{project.title}] | PostgreSQL")

            # Poblar árbol y corcho
            self.binder.populate_from_db(project.id)
            self.corkboard.populate_from_db(project.id)

            # Cargar primera escena en el editor si existe
            if project.scenes:
                first_scene = project.scenes[0]
                self.load_scene(first_scene.id)
        finally:
            db.close()

    def load_scene(self, scene_id: int):
        """Carga una escena específica desde PostgreSQL al editor y al inspector."""
        db = SessionLocal()
        try:
            scene = get_scene(db, scene_id)
            if not scene:
                return

            self._is_loading_scene = True
            self.current_scene_id = scene.id

            # Asegurar que el espacio de trabajo activo sea el editor
            if self.center_stack.currentIndex() == 3:
                self._set_workspace(0)

            # Cargar texto en editor
            self.screenplay_editor.setPlainText(scene.content or "")
            self.novel_editor.setPlainText(scene.content or "")

            # Cargar en inspector
            self.inspector.load_scene_data(scene)

            # Actualizar barra de estado
            self.lbl_scene_stat.setText(f"🎬 {scene.scene_number}. {scene.title}")
            self._is_loading_scene = False
        finally:
            db.close()

    def open_character_sheet(self, character_id: int):
        """Abre la ficha completa de psicología y biografía del personaje."""
        self.character_sheet.load_character(character_id)
        self._set_workspace(3)
        self.lbl_scene_stat.setText("👤 Editando Ficha de Personaje")

    def _on_scene_deleted(self, deleted_id: int):
        """Maneja la eliminación de una escena de PostgreSQL."""
        if self.current_scene_id == deleted_id:
            db = SessionLocal()
            try:
                acts, standalone_scenes, _, _ = get_project_acts_and_scenes(db, self.current_project_id)
                remaining_scenes = []
                for a in acts:
                    remaining_scenes.extend(a.scenes)
                remaining_scenes.extend(standalone_scenes)

                if remaining_scenes:
                    self.load_scene(remaining_scenes[0].id)
                else:
                    self.current_scene_id = None
                    self.screenplay_editor.clear()
                    self.novel_editor.clear()
                    self.lbl_scene_stat.setText("🎬 Sin escenas (usa '+' para crear una)")
            finally:
                db.close()

        # Refrescar corcho
        if self.current_project_id:
            self.corkboard.populate_from_db(self.current_project_id)

    def _on_character_saved_or_deleted(self, char_id: int):
        """Refresca el árbol y regresa al editor tras guardar o borrar un personaje."""
        if self.current_project_id:
            self.binder.populate_from_db(self.current_project_id)
        if self.center_stack.currentIndex() == 3 and not self.character_sheet.current_character_id:
            self._set_workspace(0)

    def _save_active_editor_content_to_db(self):
        """Guarda en PostgreSQL cualquier cambio escrito en el editor."""
        if self._is_loading_scene or not self.current_scene_id:
            return

        current_mode = "screenplay" if self.center_stack.currentIndex() == 0 else "novel"
        editor = self.screenplay_editor if current_mode == "screenplay" else self.novel_editor
        text = editor.toPlainText()

        db = SessionLocal()
        try:
            update_scene_content(db, self.current_scene_id, text)
        finally:
            db.close()

    def _save_scene_metadata_to_db(self, data: dict):
        """Guarda en PostgreSQL las ediciones hechas en el Inspector."""
        scene_id = data.get("scene_id")
        if not scene_id:
            return

        update_fields = {k: v for k, v in data.items() if k != "scene_id"}
        db = SessionLocal()
        try:
            update_scene_metadata(db, scene_id, **update_fields)
            if self.current_project_id:
                self.corkboard.populate_from_db(self.current_project_id)
        finally:
            db.close()

    def _get_document_context(self) -> dict:
        """Extrae el estado en vivo de PostgreSQL, personajes enriquecidos y texto para los agentes."""
        current_mode = "screenplay" if self.center_stack.currentIndex() == 0 else "novel"
        editor = self.screenplay_editor if current_mode == "screenplay" else self.novel_editor

        characters_info = []
        if self.current_project_id:
            db = SessionLocal()
            try:
                _, _, chars, _ = get_project_acts_and_scenes(db, self.current_project_id)
                for c in chars:
                    detail = f"{c.name} ({c.role}): Deseo: '{c.dramatic_need}', Defecto: '{c.fatal_flaw}'"
                    characters_info.append(detail)
            finally:
                db.close()

        return {
            "title": self.windowTitle(),
            "current_scene_title": self.lbl_scene_stat.text(),
            "current_text": editor.toPlainText(),
            "selected_text": editor.textCursor().selectedText(),
            "mode": current_mode,
            "characters": characters_info
        }

    def _insert_snippet_to_active_editor(self, snippet: str):
        """Inserta la propuesta de la IA en el documento activo y guarda en PostgreSQL."""
        if self.center_stack.currentIndex() in (2, 3):
            self._set_workspace(0)

        current_mode = "screenplay" if self.center_stack.currentIndex() == 0 else "novel"
        editor = self.screenplay_editor if current_mode == "screenplay" else self.novel_editor

        cursor = editor.textCursor()
        cursor.beginEditBlock()
        if cursor.block().text().strip():
            cursor.insertText("\n\n")
        cursor.insertText(snippet)
        cursor.insertText("\n")
        cursor.endEditBlock()
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()
        editor.setFocus()

        self._save_active_editor_content_to_db()

        QMessageBox.information(
            self,
            "Texto Insertado",
            "El fragmento sugerido por la IA ha sido insertado y guardado en PostgreSQL."
        )

    def _create_menus(self):
        menubar = self.menuBar()

        # Archivo
        file_menu = menubar.addMenu("&Archivo")
        file_menu.addAction("Nueva Escena a Tu Gusto...", self._open_new_scene_dialog, QKeySequence("Ctrl+Shift+N"))
        file_menu.addAction("Guardar Ahora en BD", self._save_active_editor_content_to_db, QKeySequence.Save)
        file_menu.addSeparator()
        export_menu = file_menu.addMenu("Exportar a...")
        export_menu.addAction("PDF (Estándar de la Industria)", self._not_implemented)
        export_menu.addAction("Fountain (.fountain)", self._not_implemented)
        export_menu.addAction("Final Draft (.fdx)", self._not_implemented)
        file_menu.addSeparator()
        file_menu.addAction("Salir", self.close, QKeySequence.Quit)

        # Global Shortcut for New Scene
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self._open_new_scene_dialog)

        # Edición
        edit_menu = menubar.addMenu("&Edición")
        edit_menu.addAction("Deshacer", self.screenplay_editor.undo, QKeySequence.Undo)
        edit_menu.addAction("Rehacer", self.screenplay_editor.redo, QKeySequence.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Cortar", self.screenplay_editor.cut, QKeySequence.Cut)
        edit_menu.addAction("Copiar", self.screenplay_editor.copy, QKeySequence.Copy)
        edit_menu.addAction("Pegar", self.screenplay_editor.paste, QKeySequence.Paste)

        # Formato (Screenplay Elements with industry shortcuts)
        fmt_menu = menubar.addMenu("&Formato")
        fmt_menu.addAction("Encabezado de Escena (Scene Heading)\tCtrl+1", lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.SCENE_HEADING))
        fmt_menu.addAction("Acción (Action)\tCtrl+2", lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.ACTION))
        fmt_menu.addAction("Personaje (Character)\tCtrl+3", lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.CHARACTER))
        fmt_menu.addAction("Paréntesis (Parenthetical)\tCtrl+4", lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.PARENTHETICAL))
        fmt_menu.addAction("Diálogo (Dialogue)\tCtrl+5", lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.DIALOGUE))
        fmt_menu.addAction("Transición (Transition)\tCtrl+6", lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.TRANSITION))

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.SCENE_HEADING))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.ACTION))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.CHARACTER))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.PARENTHETICAL))
        QShortcut(QKeySequence("Ctrl+5"), self, lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.DIALOGUE))
        QShortcut(QKeySequence("Ctrl+6"), self, lambda: self.screenplay_editor.set_current_element_type(ScriptElementType.TRANSITION))

        # Vista
        view_menu = menubar.addMenu("&Vista")
        view_menu.addAction("Alternar Binder", self._toggle_binder, QKeySequence("Ctrl+B"))
        view_menu.addAction("Alternar Inspector", self._toggle_inspector, QKeySequence("Ctrl+I"))
        view_menu.addAction("Alternar Co-Escritor IA", self._toggle_ai_dock, QKeySequence("Ctrl+J"))
        view_menu.addSeparator()
        view_menu.addAction("Modo Concentración (Zen)", self._toggle_zen_mode, QKeySequence("F11"))
        view_menu.addAction("Alternar Modo Noche en Página", self._toggle_paper_night_mode, QKeySequence("Ctrl+D"))

        # IA & Co-Escritura
        ai_menu = menubar.addMenu("&IA Agentes")
        ai_menu.addAction("Consultar Co-Escritor...", self._toggle_ai_dock)
        ai_menu.addAction("Cambiar Modelo de IA (Ollama)...", self.ai_dock._show_model_menu)
        ai_menu.addAction("Auditar Continuidad Ahora", self.inspector.continuity_tab.trigger_manual_audit)
        ai_menu.addAction("Estado de Servidor IA", self._show_ai_status)

    def _create_toolbar(self):
        toolbar = QToolBar("Barra Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 0. Nelia Brand Badge (Gold Monogram & Typography)
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(6, 0, 12, 0)
        brand_layout.setSpacing(8)

        logo_icon_lbl = QLabel()
        logo_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon_64.png")
        if os.path.exists(logo_icon_path):
            pix = QPixmap(logo_icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_icon_lbl.setPixmap(pix)
        brand_layout.addWidget(logo_icon_lbl)

        brand_lbl = QLabel("NELIA")
        brand_lbl.setStyleSheet("color: #e5a93c; font-weight: 900; font-size: 13px; letter-spacing: 2px;")
        brand_layout.addWidget(brand_lbl)

        toolbar.addWidget(brand_widget)
        toolbar.addSeparator()

        # 1. Workspace Segmented Switcher
        from PySide6.QtWidgets import QButtonGroup
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        self.btn_mode_screenplay = QPushButton("🎬 Guion")
        self.btn_mode_screenplay.setProperty("class", "mode-pill")
        self.btn_mode_screenplay.setCheckable(True)
        self.btn_mode_screenplay.setChecked(True)
        self.mode_group.addButton(self.btn_mode_screenplay, 0)
        toolbar.addWidget(self.btn_mode_screenplay)

        self.btn_mode_novel = QPushButton("📖 Novela")
        self.btn_mode_novel.setProperty("class", "mode-pill")
        self.btn_mode_novel.setCheckable(True)
        self.mode_group.addButton(self.btn_mode_novel, 1)
        toolbar.addWidget(self.btn_mode_novel)

        self.btn_mode_corkboard = QPushButton("🗂️ Beat Board")
        self.btn_mode_corkboard.setProperty("class", "mode-pill")
        self.btn_mode_corkboard.setCheckable(True)
        self.mode_group.addButton(self.btn_mode_corkboard, 2)
        toolbar.addWidget(self.btn_mode_corkboard)

        self.btn_mode_chars = QPushButton("👤 Personajes")
        self.btn_mode_chars.setProperty("class", "mode-pill")
        self.btn_mode_chars.setCheckable(True)
        self.mode_group.addButton(self.btn_mode_chars, 3)
        toolbar.addWidget(self.btn_mode_chars)

        self.mode_group.idClicked.connect(self._set_workspace)

        toolbar.addSeparator()

        # Botón destacado: + Escena a tu gusto
        self.btn_new_scene = QPushButton("🎬 + Escena")
        self.btn_new_scene.setToolTip("Añadir nueva escena personalizada a tu gusto (Ctrl+Shift+N)")
        self.btn_new_scene.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #e5a93c;
                border: 1px solid #d99b26;
                border-radius: 6px;
                padding: 5px 12px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e5a93c;
                color: #09090b;
            }
        """)
        self.btn_new_scene.clicked.connect(lambda: self._open_new_scene_dialog())
        toolbar.addWidget(self.btn_new_scene)

        toolbar.addSeparator()

        # 2. Screenplay Element Selector Dropdown
        toolbar.addWidget(QLabel(" Elemento: "))
        self.combo_element = QComboBox()
        self.combo_element.addItem("Encabezado (INT/EXT)", ScriptElementType.SCENE_HEADING)
        self.combo_element.addItem("Acción", ScriptElementType.ACTION)
        self.combo_element.addItem("Personaje", ScriptElementType.CHARACTER)
        self.combo_element.addItem("Paréntesis", ScriptElementType.PARENTHETICAL)
        self.combo_element.addItem("Diálogo", ScriptElementType.DIALOGUE)
        self.combo_element.addItem("Transición", ScriptElementType.TRANSITION)
        self.combo_element.currentIndexChanged.connect(self._on_combo_element_changed)
        toolbar.addWidget(self.combo_element)

        toolbar.addSeparator()

        # 3. AI Co-Writer Toggle Button
        self.btn_toggle_ai = QPushButton("🤖 Co-Escritor IA")
        self.btn_toggle_ai.setProperty("class", "btn-subtle")
        self.btn_toggle_ai.setToolTip("Abrir panel de chat con Co-Escritor y Arquitecto de Tramas (Ctrl+J)")
        self.btn_toggle_ai.clicked.connect(self._toggle_ai_dock)
        toolbar.addWidget(self.btn_toggle_ai)

        btn_night = QPushButton("🌙 Modo Noche")
        btn_night.setProperty("class", "btn-subtle")
        btn_night.clicked.connect(self._toggle_paper_night_mode)
        toolbar.addWidget(btn_night)

        btn_zen = QPushButton("🎯 Zen (F11)")
        btn_zen.setProperty("class", "btn-subtle")
        btn_zen.clicked.connect(self._toggle_zen_mode)
        toolbar.addWidget(btn_zen)

        # Stretch to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # Quick Export button
        btn_export = QPushButton("⚡ Exportar...")
        btn_export.setProperty("class", "btn-subtle")
        btn_export.clicked.connect(lambda: QMessageBox.information(self, "Exportación", "Módulo de exportación profesional compatible con:\n- PDF Estándar (1 pág = 1 min)\n- Final Draft (.fdx)\n- Formato Fuente (.fountain)"))
        toolbar.addWidget(btn_export)

    def _create_statusbar(self):
        sb = self.statusBar()
        self.lbl_scene_stat = QLabel("🎬 Conectado a PostgreSQL...")
        sb.addWidget(self.lbl_scene_stat)

        # Stats pill (Words, Pages, Screen Time)
        self.lbl_metrics = QLabel(" 0 palabras | Pág. 1 (~0s) ")
        self.lbl_metrics.setObjectName("StatsPill")
        sb.addPermanentWidget(self.lbl_metrics)

        # Continuity status pill
        self.lbl_continuity_status = QLabel("🟢 Continuidad OK")
        self.lbl_continuity_status.setStyleSheet("color: #34d399; font-weight: 600; padding: 0 6px;")
        sb.addPermanentWidget(self.lbl_continuity_status)

        self.lbl_element_badge = QLabel("Elemento: SCENE_HEADING")
        sb.addPermanentWidget(self.lbl_element_badge)

    def _connect_signals(self):
        # Element format and statistics
        self.screenplay_editor.elementChanged.connect(self._on_editor_element_changed)
        self.screenplay_editor.statsChanged.connect(self._on_screenplay_stats_changed)

        # Auto-save debouncer for writing (saves to PostgreSQL 700ms after user pauses typing)
        self.editor_save_timer = QTimer(self)
        self.editor_save_timer.setSingleShot(True)
        self.editor_save_timer.timeout.connect(self._save_active_editor_content_to_db)

        # Debounced continuity trigger on text modification (3.8s)
        self.continuity_debounce_timer = QTimer(self)
        self.continuity_debounce_timer.setSingleShot(True)
        self.continuity_debounce_timer.timeout.connect(self._on_continuity_debounce_timeout)

        self.screenplay_editor.textChanged.connect(self._on_text_modified)
        self.novel_editor.textChanged.connect(self._on_text_modified)

        # Binder item selection and actions
        self.binder.sceneSelected.connect(self.load_scene)
        self.binder.characterSelected.connect(self.open_character_sheet)
        self.binder.sceneDeleted.connect(self._on_scene_deleted)

        # Corkboard card click and creation
        self.corkboard.cardSelected.connect(self.load_scene)
        self.corkboard.sceneCreated.connect(self.load_scene)
        self.binder.structureChanged.connect(lambda: self.corkboard.populate_from_db(self.current_project_id))

        # Character Sheet signals
        self.character_sheet.characterSaved.connect(self._on_character_saved_or_deleted)
        self.character_sheet.characterDeleted.connect(self._on_character_saved_or_deleted)

        # Inspector metadata modifications -> save to PostgreSQL
        self.inspector.metadataChanged.connect(self._save_scene_metadata_to_db)

        # Continuity status update
        self.inspector.continuity_tab.statusUpdated.connect(self._on_continuity_status_updated)

    def _open_new_scene_dialog(self, act_id: int = None):
        """Abre el diálogo para crear una escena personalizada con slugline builder y metadatos."""
        if not self.current_project_id:
            return
        from widgets.new_scene_dialog import NewSceneDialog
        dlg = NewSceneDialog(
            project_id=self.current_project_id,
            current_scene_id=self.current_scene_id,
            default_act_id=act_id,
            parent=self
        )
        if dlg.exec():
            if dlg.created_scene_id:
                self.binder.populate_from_db(self.current_project_id)
                self.corkboard.populate_from_db(self.current_project_id)
                self.load_scene(dlg.created_scene_id)

    def _on_text_modified(self):
        if not self._is_loading_scene:
            self.editor_save_timer.start(700)
            self.continuity_debounce_timer.start(3800)

    def _on_continuity_debounce_timeout(self):
        self.inspector.continuity_tab.trigger_manual_audit()

    def _on_continuity_status_updated(self, status: str):
        if status == "OK":
            self.lbl_continuity_status.setText("🟢 Continuidad OK")
            self.lbl_continuity_status.setStyleSheet("color: #34d399; font-weight: 600; padding: 0 6px;")
        else:
            self.lbl_continuity_status.setText("🟡 Revisión Sugerida")
            self.lbl_continuity_status.setStyleSheet("color: #fbbf24; font-weight: 600; padding: 0 6px;")

    def _set_workspace(self, index: int):
        self.center_stack.setCurrentIndex(index)
        self.btn_mode_screenplay.setChecked(index == 0)
        self.btn_mode_novel.setChecked(index == 1)
        self.btn_mode_corkboard.setChecked(index == 2)
        self.btn_mode_chars.setChecked(index == 3)

        self.combo_element.setEnabled(index == 0)

        # Si entra al corcho, refrescar las tarjetas desde PostgreSQL
        if index == 2 and self.current_project_id:
            self.corkboard.populate_from_db(self.current_project_id)
        # Si entra a personajes sin seleccionar uno, abrir el primero si existe
        elif index == 3 and not self.character_sheet.current_character_id and self.current_project_id:
            db = SessionLocal()
            try:
                _, _, chars, _ = get_project_acts_and_scenes(db, self.current_project_id)
                if chars:
                    self.character_sheet.load_character(chars[0].id)
            finally:
                db.close()

    def _on_combo_element_changed(self):
        elem_code = self.combo_element.currentData()
        if elem_code:
            self.screenplay_editor.set_current_element_type(elem_code)

    def _on_editor_element_changed(self, elem_code: str):
        self.combo_element.blockSignals(True)
        idx = self.combo_element.findData(elem_code)
        if idx >= 0:
            self.combo_element.setCurrentIndex(idx)
        self.combo_element.blockSignals(False)
        self.lbl_element_badge.setText(f"Elemento: {elem_code}")

    def _on_screenplay_stats_changed(self, words: int, scenes: int):
        pages = max(1, round(words / 220, 1))
        mins = int(pages)
        secs = int((pages - mins) * 60)
        self.lbl_metrics.setText(f" 📊 {words} palabras | {pages} págs (~{mins}m {secs}s) ")

    def _toggle_binder(self):
        self.binder.setVisible(not self.binder.isVisible())

    def _toggle_inspector(self):
        self.inspector.setVisible(not self.inspector.isVisible())

    def _toggle_ai_dock(self):
        self.ai_dock.setVisible(not self.ai_dock.isVisible())

    def _toggle_zen_mode(self):
        is_zen = not self.binder.isVisible() and not self.inspector.isVisible() and not self.ai_dock.isVisible()
        if is_zen:
            self.binder.setVisible(True)
            self.inspector.setVisible(True)
            self.ai_dock.setVisible(True)
        else:
            self.binder.setVisible(False)
            self.inspector.setVisible(False)
            self.ai_dock.setVisible(False)

    def _toggle_paper_night_mode(self):
        is_dark = not self.screenplay_editor.is_dark_paper
        self.screenplay_page.set_dark_mode(is_dark)
        self.novel_page.set_dark_mode(is_dark)

    def _show_ai_status(self):
        url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/status"
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                data = resp.read().decode()
                QMessageBox.information(self, "Estado del Servidor IA", f"Respuesta del servicio FastAPI:\n\n{data}")
        except Exception as e:
            QMessageBox.warning(self, "Servidor IA", f"No se pudo consultar el estado: {e}")

    def _not_implemented(self):
        QMessageBox.information(self, "Información", "Función en desarrollo en el pipeline de producción.")

    def closeEvent(self, event):
        self._save_active_editor_content_to_db()
        if self.server_process:
            try:
                self.server_process.terminate()
            except Exception:
                pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon_256.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.setStyleSheet(DARK_THEME_QSS)

    window = ScriptorStudioWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
