from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFileDialog

class TranscribeView(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        
        heading = QLabel("Transcribe media")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Tạo file SRT từ audio hoặc video bằng Whisper local."))
        
        self.media_path = QLineEdit()
        self.media_path.setPlaceholderText("File audio/video")
        self.main_window.media_path = self.media_path
        self.main_window.operation_controls.append(self.media_path)
        
        choose = QPushButton("Chọn media")
        choose.clicked.connect(self._choose_media)
        self.main_window.operation_controls.append(choose)
        
        row = QHBoxLayout()
        row.addWidget(self.media_path, 1)
        row.addWidget(choose)
        layout.addLayout(row)
        
        self.transcribe_output = QLineEdit("subtitle.srt")
        self.main_window.transcribe_output = self.transcribe_output
        self.main_window.operation_controls.append(self.transcribe_output)
        layout.addWidget(self.transcribe_output)
        
        run = QPushButton("Transcribe")
        run.clicked.connect(self.main_window._run_transcribe)
        self.main_window.operation_controls.append(run)
        layout.addWidget(run)
        layout.addStretch()

    def _choose_media(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn media", "", "Media files (*)")
        if path:
            self.media_path.setText(path)
            self.main_window.state.transcribe_values["source"] = path