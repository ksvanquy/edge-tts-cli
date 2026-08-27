from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit

class VoicesView(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        
        heading = QLabel("Voice catalog")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Tìm voice theo engine, locale, giới tính hoặc tên."))
        
        run = QPushButton("Load voices")
        run.clicked.connect(self.main_window._run_voices)
        self.main_window.operation_controls.append(run)
        layout.addWidget(run)
        
        self.voice_table = QPlainTextEdit()
        self.voice_table.setReadOnly(True)
        self.main_window.voice_table = self.voice_table
        self.main_window.operation_controls.append(self.voice_table)
        layout.addWidget(self.voice_table, 1)