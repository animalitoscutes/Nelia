"""
Interactive AI Co-Writer Chat Dock & Widget.
Features:
- Conversation history with dual agents (Co-Writer & Plot Architect)
- Direct 'Insertar en la Historia' button for suggested text/scenes
- Model status indicator (Qwen 2.5 7B on RTX 3060)
- Asynchronous communication with local FastAPI service
"""

import json
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QScrollArea, QWidget, QComboBox,
    QProgressBar, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QAction
import httpx


class SendMessageThread(QThread):
    responseReceived = Signal(dict)
    errorOccurred = Signal(str)

    def __init__(self, prompt: str, context_dict: dict, agent_type: str, model: str, history: list = None):
        super().__init__()
        self.prompt = prompt
        self.context_dict = context_dict
        self.agent_type = agent_type
        self.model = model
        self.history = history or []

    def run(self):
        try:
            payload = {
                "prompt": self.prompt,
                "context": self.context_dict,
                "agent_type": self.agent_type,
                "model": self.model,
                "history": self.history
            }
            from ai.config import FASTAPI_HOST, FASTAPI_PORT
            url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/chat"
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    self.responseReceived.emit(res.json())
                else:
                    self.errorOccurred.emit(f"Error HTTP {res.status_code}: {res.text}")
        except Exception as e:
            self.errorOccurred.emit(f"No se pudo conectar con el servidor IA: {str(e)}")


class ChatMessageBubble(QFrame):
    insertRequested = Signal(str)

    def __init__(self, role: str, text: str, snippet: str = None, model_name: str = None, agent_type: str = "cowriter", parent=None):
        super().__init__(parent)
        self.snippet = snippet
        self.setObjectName("ChatBubble")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header: Role & tag
        header = QHBoxLayout()
        if role == "user":
            lbl_role = QLabel("👤 TÚ (AUTOR)")
            lbl_role.setStyleSheet("color: #e5a93c; font-weight: 700; font-size: 11px;")
            self.setStyleSheet("""
                QFrame#ChatBubble {
                    background-color: #202027;
                    border: 1px solid #32323f;
                    border-radius: 8px;
                    margin-left: 20px;
                }
            """)
        else:
            if agent_type == "architect":
                tag = f"🧠 ARQUITECTO DE TRAMAS ({model_name})" if model_name else "🧠 ARQUITECTO DE TRAMAS"
                lbl_role = QLabel(tag)
                lbl_role.setStyleSheet("color: #c084fc; font-weight: 700; font-size: 11px;")
                self.setStyleSheet("""
                    QFrame#ChatBubble {
                        background-color: #1a1528;
                        border: 1px solid #3b2d54;
                        border-left: 3px solid #c084fc;
                        border-radius: 8px;
                        margin-right: 20px;
                    }
                """)
            else:
                tag = f"🎬 CO-ESCRITOR IA ({model_name})" if model_name else "🎬 CO-ESCRITOR IA"
                lbl_role = QLabel(tag)
                lbl_role.setStyleSheet("color: #60a5fa; font-weight: 700; font-size: 11px;")
                self.setStyleSheet("""
                    QFrame#ChatBubble {
                        background-color: #17171d;
                        border: 1px solid #272732;
                        border-left: 3px solid #60a5fa;
                        border-radius: 8px;
                        margin-right: 20px;
                    }
                """)
        header.addWidget(lbl_role)
        header.addStretch()
        layout.addLayout(header)

        # Body text (stripping the XML tag from display for visual cleanliness)
        clean_text = text.replace("<TEXTO_HISTORIA>", "\n📝 [PROPUESTA DE TEXTO]:\n").replace("</TEXTO_HISTORIA>", "")
        lbl_text = QLabel(clean_text)
        lbl_text.setWordWrap(True)
        lbl_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl_text.setStyleSheet("color: #f4f4f5; font-size: 12px; line-height: 1.4;")
        layout.addWidget(lbl_text)

        # If a story snippet was extracted or detected, provide the 1-click Insert button
        if snippet:
            btn_layout = QHBoxLayout()
            btn_insert = QPushButton("➕ Mandar al Guion / Historia")
            btn_insert.setCursor(Qt.PointingHandCursor)
            btn_insert.setStyleSheet("""
                QPushButton {
                    background-color: #e5a93c;
                    color: #09090b;
                    font-weight: 700;
                    font-size: 11px;
                    border-radius: 4px;
                    padding: 5px 12px;
                }
                QPushButton:hover {
                    background-color: #f59e0b;
                }
            """)
            btn_insert.clicked.connect(lambda: self.insertRequested.emit(snippet))
            btn_layout.addWidget(btn_insert)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)


class AIChatDock(QFrame):
    insertSnippetToDocument = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AIChatDock")
        self.setProperty("class", "panel-sidebar")
        self.current_model = "qwen2.5:7b"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # 1. Header with Title & Dynamic Model Selector
        header = QHBoxLayout()
        title = QLabel("🤖 CO-ESCRITOR IA")
        title.setProperty("class", "panel-header-title")
        header.addWidget(title)
        header.addStretch()

        self.btn_model_select = QPushButton(f"⚡ {self.current_model} ▾")
        self.btn_model_select.setCursor(Qt.PointingHandCursor)
        self.btn_model_select.setToolTip("Haz clic para cambiar el modelo de Ollama instalado")
        self.btn_model_select.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 4px;
                border: 1px solid #0284c7;
            }
            QPushButton:hover {
                background-color: #0369a1;
                color: #ffffff;
            }
        """)
        self.btn_model_select.clicked.connect(self._show_model_menu)
        header.addWidget(self.btn_model_select)
        layout.addLayout(header)

        # 2. Agent Focus selector + Clear Chat Button
        sub_header = QHBoxLayout()
        sub_header.addWidget(QLabel("Modo:"))
        self.combo_agent = QComboBox()
        self.combo_agent.addItem("🎬 Co-Escritor (Escenas y Diálogos)", "cowriter")
        self.combo_agent.addItem("🧠 Arquitecto (Tramas y Personajes)", "architect")
        self.combo_agent.currentIndexChanged.connect(self._on_agent_mode_changed)
        sub_header.addWidget(self.combo_agent, 1)

        self.btn_clear_chat = QPushButton("🧹")
        self.btn_clear_chat.setToolTip("Limpiar conversación para empezar de cero con otra idea")
        self.btn_clear_chat.setCursor(Qt.PointingHandCursor)
        self.btn_clear_chat.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #a1a1aa;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dc2626;
                color: #ffffff;
            }
        """)
        self.btn_clear_chat.clicked.connect(self.clear_conversation)
        sub_header.addWidget(self.btn_clear_chat)
        layout.addLayout(sub_header)

        # 3. Small explanatory message explaining what the function does (non-intrusive)
        self.lbl_help = QLabel("Sugerencias de escenas, diálogos y giros dramáticos en tiempo real con inserción directa en el guion.")
        self.lbl_help.setWordWrap(True)
        self.lbl_help.setStyleSheet("color: #71717a; font-size: 11px; line-height: 1.3; padding: 2px 2px 4px 2px;")
        layout.addWidget(self.lbl_help)

        # 4. Chat History Area (Clean start without bloated welcome box)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #111114; border: 1px solid #23232a; border-radius: 6px;")

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # 5. Progress / Loading Bar (Hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #e5a93c; }")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 6. Input Text & Send
        input_container = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Pregunta, pide una escena o un giro...")
        self.input_edit.setProperty("class", "inspector-field")
        self.input_edit.returnPressed.connect(self._send_message)
        input_container.addWidget(self.input_edit)

        self.btn_send = QPushButton("Enviar")
        self.btn_send.setProperty("class", "mode-pill")
        self.btn_send.clicked.connect(self._send_message)
        input_container.addWidget(self.btn_send)
        layout.addLayout(input_container)

        self.context_provider = None
        self.current_thread = None
        self.chat_history: list[dict] = []

    def set_context_provider(self, func):
        """Callback to fetch real-time document context from the editor."""
        self.context_provider = func

    def _fetch_available_models(self) -> list[str]:
        """Consulta en tiempo real a Ollama los modelos disponibles instalados."""
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get("http://localhost:11434/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = []
                    for m in data.get("models", []):
                        name = m.get("name", "")
                        # Ignorar modelos exclusivos de embedding como nomic-embed
                        if "embed" in name.lower() or "bert" in name.lower():
                            continue
                        models.append(name)
                    if models:
                        return models
        except Exception:
            pass
        return ["qwen2.5:7b"]

    def _show_model_menu(self):
        """Muestra un menú contextual desplegable con todos los modelos locales de Ollama."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #18181b;
                color: #f4f4f5;
                border: 1px solid #3f3f46;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 18px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e5a93c;
                color: #09090b;
                font-weight: 600;
            }
            QMenu::separator {
                height: 1px;
                background-color: #27272a;
                margin: 4px 6px;
            }
        """)

        models = self._fetch_available_models()
        hdr = menu.addAction("Modelos de Ollama instalados:")
        hdr.setEnabled(False)
        menu.addSeparator()

        for m in models:
            prefix = "● " if m == self.current_model else "   "
            act = menu.addAction(f"{prefix}{m}")
            act.setData(m)

        menu.addSeparator()
        refresh_act = menu.addAction("🔄 Refrescar lista de modelos...")

        pos = self.btn_model_select.mapToGlobal(self.btn_model_select.rect().bottomLeft())
        chosen = menu.exec(pos)
        if chosen:
            if chosen == refresh_act:
                self._show_model_menu()
            elif chosen.data():
                self.set_active_model(chosen.data())

    def set_active_model(self, model_name: str):
        """Cambia el modelo activo y notifica al backend FastAPI."""
        self.current_model = model_name
        self.btn_model_select.setText(f"⚡ {model_name} ▾")
        try:
            from ai.config import FASTAPI_HOST, FASTAPI_PORT
            url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/set-model"
            with httpx.Client(timeout=1.5) as client:
                client.post(url, json={"model_name": model_name})
        except Exception:
            pass

    def _on_agent_mode_changed(self):
        agent_type = self.combo_agent.currentData()
        if agent_type == "architect":
            self.lbl_help.setText("🧠 Modo Arquitecto: Diseño conceptual de tramas, premisas, arcos dramáticos y psicología de personajes.")
        else:
            self.lbl_help.setText("🎬 Modo Co-Escritor: Redacción de escenas, diálogos verosímiles y acciones listas para el guion.")

    def clear_conversation(self):
        """Limpia la memoria y los mensajes del chat para empezar un nuevo hilo."""
        self.chat_history.clear()
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_bubble(self, role: str, text: str, snippet: str = None, model_name: str = None, agent_type: str = "cowriter"):
        bubble = ChatMessageBubble(role, text, snippet, model_name=model_name, agent_type=agent_type)
        bubble.insertRequested.connect(self.insertSnippetToDocument.emit)
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def _send_message(self):
        text = self.input_edit.text().strip()
        if not text:
            return

        self.input_edit.clear()
        agent_type = self.combo_agent.currentData()
        self._add_bubble("user", text, agent_type=agent_type)

        # Guardar en memoria de conversación para mantener contexto multi-turno
        self.chat_history.append({"role": "user", "content": text})

        # Gather context
        context_dict = {}
        if self.context_provider:
            context_dict = self.context_provider()

        self.btn_send.setEnabled(False)
        self.progress_bar.show()

        # Run in background QThread to keep PySide6 GUI responsive
        self.current_thread = SendMessageThread(
            prompt=text,
            context_dict=context_dict,
            agent_type=agent_type,
            model=self.current_model,
            history=list(self.chat_history)
        )
        self.current_thread.responseReceived.connect(self._on_response)
        self.current_thread.errorOccurred.connect(self._on_error)
        self.current_thread.finished.connect(lambda: [
            self.btn_send.setEnabled(True),
            self.progress_bar.hide()
        ])
        self.current_thread.start()

    def _on_response(self, data: dict):
        reply = data.get("reply", "")
        snippet = data.get("suggested_snippet")
        model_used = data.get("model_used", self.current_model)
        agent_used = data.get("agent_used", self.combo_agent.currentData())
        
        self.chat_history.append({"role": "assistant", "content": reply})
        self._add_bubble("assistant", reply, snippet, model_name=model_used, agent_type=agent_used)

    def _on_error(self, err_msg: str):
        agent_type = self.combo_agent.currentData()
        self._add_bubble("assistant", f"⚠️ {err_msg}", model_name=self.current_model, agent_type=agent_type)
