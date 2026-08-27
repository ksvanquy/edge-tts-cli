from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFileDialog

class BatchView(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        
        heading = QLabel("Batch processing")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Xử lý file TXT, SRT hoặc VTT theo thứ tự."))
        
        self.batch_directory = QLineEdit(str(self.main_window.state.batch_values["directory"]))
        self.batch_directory.setPlaceholderText("Thư mục nguồn")
        self.main_window.batch_directory = self.batch_directory
        self.main_window.operation_controls.append(self.batch_directory)
        
        choose = QPushButton("Chọn thư mục")
        choose.clicked.connect(self._choose_batch_directory)
        self.main_window.operation_controls.append(choose)
        
        row = QHBoxLayout()
        row.addWidget(self.batch_directory, 1)
        row.addWidget(choose)
        layout.addLayout(row)
        
        start = QPushButton("Start batch")
        start.clicked.connect(self.main_window._run_batch)
        self.main_window.operation_controls.append(start)
        layout.addWidget(start)
        layout.addStretch()

    def _choose_batch_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục nguồn")
        if path:
            self.batch_directory.setText(path)
            self.main_window.state.batch_values["directory"] = path
            self.main_window.state.save_to_file()