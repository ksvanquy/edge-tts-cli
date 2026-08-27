from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QLabel, QPushButton, QFileDialog

class GenerateView(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        
        heading = QLabel("Generate audio")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Nhập văn bản hoặc chọn một file TXT, SRT, VTT."))
        
        self.text_editor = QPlainTextEdit()
        self.text_editor.setPlaceholderText("Text trực tiếp")
        self.text_editor.setMinimumHeight(300)
        self.text_editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_editor)
        self.main_window.operation_controls.append(self.text_editor)
        
        file_row = QHBoxLayout()
        self.file_label = QLabel("Chưa chọn file")
        choose = QPushButton("Chọn file")
        choose.clicked.connect(self._choose_input_file)
        self.main_window.operation_controls.append(choose)
        file_row.addWidget(self.file_label, 1)
        file_row.addWidget(choose)
        layout.addLayout(file_row)
        
        generate = QPushButton("Generate")
        generate.clicked.connect(self.main_window._run_generate)
        self.main_window.operation_controls.append(generate)
        layout.addWidget(generate)
        layout.addStretch()

    def _on_text_changed(self) -> None:
        # Khi người dùng gõ text trực tiếp, tự động xóa file đã chọn trước đó
        if self.text_editor.toPlainText().strip():
            self.main_window.state.generate_values["file"] = ""
            self.file_label.setText("Chưa chọn file")

    def _choose_input_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn input", "", "Text/subtitle (*.txt *.srt *.vtt)")
        if path:
            self.main_window.state.generate_values["file"] = path
            self.main_window.state.generate_values["text"] = ""
            self.text_editor.blockSignals(True)
            self.text_editor.clear()
            self.text_editor.blockSignals(False)
            self.file_label.setText(Path(path).name)