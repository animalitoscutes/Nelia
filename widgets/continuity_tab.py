"""
Continuity Auditor & Script Doctor Tab Widget.
Monitors the story in real-time and alerts about:
- Inconsistencies, plot holes, and timeline breaks
- Character voice and motivation drift
- Actionable suggestions
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor
import httpx
import datetime


class ContinuityThread(QThread):
    analysisDone = Signal(dict)
    errorOccurred = Signal(str)

    def __init__(self, context_dict: dict):
        super().__init__()
        self.context_dict = context_dict

    def run(self):
        try:
            payload = {
                "context": self.context_dict,
                "model": None # Utiliza el modelo activo seleccionado por el usuario en FastAPI
            }
            from ai.config import FASTAPI_HOST, FASTAPI_PORT
            url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/analyze-continuity"
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    self.analysisDone.emit(res.json())
                else:
                    self.errorOccurred.emit(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            self.errorOccurred.emit(str(e))


class ContinuityTabWidget(QWidget):
    statusUpdated = Signal(str) # Emits "OK" or "ATENCION"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 10, 6, 6)
        layout.setSpacing(8)

        # 1. Status Indicator Card
        self.status_card = QWidget()
        self.status_card.setStyleSheet("""
            QWidget {
                background-color: #172554;
                border: 1px solid #1e40af;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        card_lay = QVBoxLayout(self.status_card)
        card_lay.setContentsMargins(8, 6, 8, 6)
        card_lay.setSpacing(4)

        self.lbl_status_badge = QLabel("🟢 CONTINUIDAD: SÓLIDA")
        self.lbl_status_badge.setStyleSheet("color: #60a5fa; font-weight: 700; font-size: 11px;")
        card_lay.addWidget(self.lbl_status_badge)

        self.lbl_time = QLabel("Esperando primer cambio...")
        self.lbl_time.setStyleSheet("color: #94a3b8; font-size: 10px;")
        card_lay.addWidget(self.lbl_time)
        layout.addWidget(self.status_card)

        # 2. Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #38bdf8; }")
        self.progress.hide()
        layout.addWidget(self.progress)

        # 3. Report View
        lbl_rep = QLabel("INFORME DEL SCRIPT DOCTOR:")
        lbl_rep.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: 600;")
        layout.addWidget(lbl_rep)

        self.report_edit = QTextEdit()
        self.report_edit.setReadOnly(True)
        self.report_edit.setProperty("class", "inspector-field")
        self.report_edit.setPlaceholderText("El agente de continuidad analizará tu texto automáticamente cada vez que pauses la escritura...")
        layout.addWidget(self.report_edit)

        # 4. Manual Audit Trigger Button
        self.btn_audit = QPushButton("🔍 Auditar Continuidad Ahora")
        self.btn_audit.setProperty("class", "btn-subtle")
        self.btn_audit.clicked.connect(self.trigger_manual_audit)
        layout.addWidget(self.btn_audit)

        self.context_provider = None
        self.thread = None

    def set_context_provider(self, func):
        self.context_provider = func

    def trigger_manual_audit(self):
        if not self.context_provider:
            return
        context_dict = self.context_provider()
        if not context_dict or not context_dict.get("current_text", "").strip():
            return

        self.btn_audit.setEnabled(False)
        self.progress.show()
        self.lbl_time.setText("Auditando lógica de la escena...")

        self.thread = ContinuityThread(context_dict)
        self.thread.analysisDone.connect(self._on_done)
        self.thread.errorOccurred.connect(self._on_error)
        self.thread.finished.connect(lambda: [
            self.btn_audit.setEnabled(True),
            self.progress.hide()
        ])
        self.thread.start()

    def _on_done(self, data: dict):
        status = data.get("status", "OK")
        report = data.get("report", "")
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        self.report_edit.setPlainText(report)
        self.lbl_time.setText(f"Última auditoría: {now_str} (Qwen 2.5 7B)")

        if status == "OK":
            self.lbl_status_badge.setText("🟢 CONTINUIDAD: SÓLIDA")
            self.status_card.setStyleSheet("""
                background-color: #064e3b;
                border: 1px solid #059669;
                border-radius: 6px;
            """)
            self.lbl_status_badge.setStyleSheet("color: #34d399; font-weight: 700; font-size: 11px;")
        else:
            self.lbl_status_badge.setText("🟡 CONTINUIDAD: ATENCIÓN")
            self.status_card.setStyleSheet("""
                background-color: #451a03;
                border: 1px solid #d97706;
                border-radius: 6px;
            """)
            self.lbl_status_badge.setStyleSheet("color: #fbbf24; font-weight: 700; font-size: 11px;")

        self.statusUpdated.emit(status)

    def _on_error(self, err: str):
        self.lbl_time.setText("Error al conectar con el agente.")
        self.report_edit.setPlainText(f"No se pudo completar el análisis: {err}\n\nAsegúrate de que el servidor FastAPI esté iniciado.")
