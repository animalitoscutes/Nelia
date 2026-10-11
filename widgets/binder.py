"""
The Binder (Project Navigator).
Loads live structure from PostgreSQL:
- Acts and Scenes
- Characters
- Worldbuilding / Lore Items
Full Management:
- Add new scenes and characters
- Delete scenes and characters (Button, Context Menu, Delete key)
- Rename items
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QInputDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from db.database import SessionLocal
from db.crud import (
    get_project_acts_and_scenes, create_new_scene, delete_scene,
    create_character, delete_character, update_scene_metadata
)


class BinderWidget(QFrame):
    sceneSelected = Signal(int)       # Emits real PostgreSQL scene_id
    characterSelected = Signal(int)   # Emits real PostgreSQL character_id
    sceneDeleted = Signal(int)        # Emits deleted scene_id
    structureChanged = Signal()       # Emits when an item was added or deleted

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BinderPanel")
        self.setProperty("class", "panel-sidebar")
        self.current_project_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header Title and Action Buttons
        header_layout = QHBoxLayout()
        title = QLabel("ESTRUCTURA & BINDER")
        title.setProperty("class", "panel-header-title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add Button with Menu (+ Escena, + Personaje)
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(24, 24)
        self.add_btn.setToolTip("Añadir nueva escena o personaje a PostgreSQL")
        self.add_btn.setProperty("class", "btn-subtle")
        self.add_btn.clicked.connect(self._show_add_menu)
        header_layout.addWidget(self.add_btn)

        # Delete Button (🗑️)
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip("Eliminar elemento seleccionado (Supr)")
        self.delete_btn.setProperty("class", "btn-subtle")
        self.delete_btn.clicked.connect(self._delete_selected_item)
        header_layout.addWidget(self.delete_btn)

        layout.addLayout(header_layout)

        # Quick Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filtrar escenas o personajes...")
        self.search_input.setProperty("class", "inspector-field")
        self.search_input.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_input)

        # Tree Widget with Custom Context Menu
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

    def populate_from_db(self, project_id: int):
        """Carga la estructura en vivo desde PostgreSQL."""
        self.current_project_id = project_id
        self.tree.clear()

        db = SessionLocal()
        try:
            acts, standalone_scenes, characters, lore = get_project_acts_and_scenes(db, project_id)

            # 1. Raíz del Guion
            script_root = QTreeWidgetItem(self.tree, ["🎬 GUION / MANUSCRITO"])
            script_root.setData(0, Qt.UserRole + 1, ("root_script", 0))
            script_root.setExpanded(True)

            for act in acts:
                act_item = QTreeWidgetItem(script_root, [f"📁 {act.title}"])
                act_item.setData(0, Qt.UserRole + 1, ("act", act.id))
                act_item.setExpanded(True)

                for sc in act.scenes:
                    sc_item = QTreeWidgetItem(act_item, [f"{sc.scene_number}. {sc.title}"])
                    sc_item.setData(0, Qt.UserRole, sc.id) # scene_id
                    sc_item.setData(0, Qt.UserRole + 1, ("scene", sc.id))

            for sc in standalone_scenes:
                sc_item = QTreeWidgetItem(script_root, [f"{sc.scene_number}. {sc.title}"])
                sc_item.setData(0, Qt.UserRole, sc.id)
                sc_item.setData(0, Qt.UserRole + 1, ("scene", sc.id))

            # 2. Personajes
            chars_root = QTreeWidgetItem(self.tree, ["👥 PERSONAJES REGISTRADOS"])
            chars_root.setData(0, Qt.UserRole + 1, ("root_chars", 0))
            chars_root.setExpanded(True)
            for c in characters:
                c_item = QTreeWidgetItem(chars_root, [f"👤 {c.name} ({c.role})"])
                c_item.setData(0, Qt.UserRole + 1, ("character", c.id))

            # 3. Lore e Investigación
            if lore:
                lore_root = QTreeWidgetItem(self.tree, ["🌍 INVESTIGACIÓN & LORE"])
                for l in lore:
                    l_item = QTreeWidgetItem(lore_root, [f"📄 {l.title}"])
                    l_item.setData(0, Qt.UserRole + 1, ("lore", l.id))
        finally:
            db.close()

    def _on_item_clicked(self, item, column):
        meta = item.data(0, Qt.UserRole + 1)
        if not meta:
            return

        item_type, item_id = meta
        if item_type == "scene":
            self.sceneSelected.emit(item_id)
        elif item_type == "character":
            self.characterSelected.emit(item_id)

    def _show_add_menu(self):
        menu = QMenu(self)
        act_scene = menu.addAction("🎬 Nueva Escena")
        act_char = menu.addAction("👤 Nuevo Personaje")
        
        chosen = menu.exec(self.add_btn.mapToGlobal(self.add_btn.rect().bottomLeft()))
        if chosen == act_scene:
            self._add_scene_dialog()
        elif chosen == act_char:
            self._add_character_dialog()

    def _add_scene_dialog(self, default_act_id=None, insert_after_scene_id=None):
        if not self.current_project_id:
            return
        from widgets.new_scene_dialog import NewSceneDialog
        dlg = NewSceneDialog(
            project_id=self.current_project_id,
            current_scene_id=insert_after_scene_id,
            default_act_id=default_act_id,
            parent=self
        )
        if dlg.exec():
            if dlg.created_scene_id:
                self.populate_from_db(self.current_project_id)
                self.sceneSelected.emit(dlg.created_scene_id)
                self.structureChanged.emit()

    def _add_character_dialog(self):
        if not self.current_project_id:
            return
        name, ok = QInputDialog.getText(
            self,
            "Nuevo Personaje",
            "Nombre del personaje:\nEj: Carlos Benítez"
        )
        if ok and name.strip():
            db = SessionLocal()
            try:
                new_char = create_character(
                    db,
                    self.current_project_id,
                    name=name.strip(),
                    role="Secundario",
                    bio="",
                    dramatic_need="",
                    fatal_flaw="",
                    dialogue_style="",
                    arc=""
                )
                self.populate_from_db(self.current_project_id)
                self.characterSelected.emit(new_char.id)
                self.structureChanged.emit()
            finally:
                db.close()

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        meta = item.data(0, Qt.UserRole + 1)
        if not meta:
            return

        item_type, item_id = meta
        menu = QMenu(self)

        if item_type == "scene":
            act_insert = menu.addAction("➕ Insertar Escena Aquí (Después)")
            act_rename = menu.addAction("✏️ Renombrar Slugline")
            menu.addSeparator()
            act_del = menu.addAction("🗑️ Eliminar Escena")
            action = menu.exec(self.tree.mapToGlobal(pos))
            if action == act_insert:
                self._add_scene_dialog(insert_after_scene_id=item_id)
            elif action == act_rename:
                self._rename_scene(item_id, item.text(0))
            elif action == act_del:
                self._delete_scene_by_id(item_id, item.text(0))

        elif item_type == "act":
            act_add = menu.addAction("➕ Añadir Escena a este Acto")
            action = menu.exec(self.tree.mapToGlobal(pos))
            if action == act_add:
                self._add_scene_dialog(default_act_id=item_id)

        elif item_type == "character":
            act_del = menu.addAction("🗑️ Eliminar Personaje")
            action = menu.exec(self.tree.mapToGlobal(pos))
            if action == act_del:
                self._delete_character_by_id(item_id, item.text(0))

        elif item_type == "root_script":
            act_add = menu.addAction("➕ Nueva Escena a tu Gusto")
            action = menu.exec(self.tree.mapToGlobal(pos))
            if action == act_add:
                self._add_scene_dialog()

        elif item_type == "root_chars":
            act_add = menu.addAction("➕ Nuevo Personaje")
            action = menu.exec(self.tree.mapToGlobal(pos))
            if action == act_add:
                self._add_character_dialog()

    def _delete_selected_item(self):
        current_item = self.tree.currentItem()
        if not current_item:
            return
        meta = current_item.data(0, Qt.UserRole + 1)
        if not meta:
            return

        item_type, item_id = meta
        if item_type == "scene":
            self._delete_scene_by_id(item_id, current_item.text(0))
        elif item_type == "character":
            self._delete_character_by_id(item_id, current_item.text(0))

    def _delete_scene_by_id(self, scene_id: int, scene_title: str):
        ans = QMessageBox.question(
            self,
            "Eliminar Escena / Hoja",
            f"¿Estás seguro de que deseas eliminar permanentemente la escena:\n\n'{scene_title}'\n\nde PostgreSQL?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            db = SessionLocal()
            try:
                delete_scene(db, scene_id)
                self.populate_from_db(self.current_project_id)
                self.sceneDeleted.emit(scene_id)
                self.structureChanged.emit()
            finally:
                db.close()

    def _delete_character_by_id(self, char_id: int, char_name: str):
        ans = QMessageBox.question(
            self,
            "Eliminar Personaje",
            f"¿Estás seguro de que deseas eliminar a '{char_name}' de PostgreSQL?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            db = SessionLocal()
            try:
                delete_character(db, char_id)
                self.populate_from_db(self.current_project_id)
                self.structureChanged.emit()
            finally:
                db.close()

    def _rename_scene(self, scene_id: int, current_name: str):
        new_title, ok = QInputDialog.getText(
            self,
            "Renombrar Escena",
            "Nuevo encabezado de escena:",
            text=current_name
        )
        if ok and new_title.strip():
            db = SessionLocal()
            try:
                update_scene_metadata(db, scene_id, title=new_title.strip())
                self.populate_from_db(self.current_project_id)
                self.sceneSelected.emit(scene_id)
                self.structureChanged.emit()
            finally:
                db.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self._delete_selected_item()
            return
        super().keyPressEvent(event)

    def _filter_items(self, text: str):
        query = text.lower()
        def search_node(node):
            node_match = query in node.text(0).lower()
            child_match = False
            for i in range(node.childCount()):
                child = node.child(i)
                if search_node(child):
                    child_match = True
            is_visible = node_match or child_match or not query
            node.setHidden(not is_visible)
            if child_match and query:
                node.setExpanded(True)
            return is_visible

        for i in range(self.tree.topLevelItemCount()):
            search_node(self.tree.topLevelItem(i))
