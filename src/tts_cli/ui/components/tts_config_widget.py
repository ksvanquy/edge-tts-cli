from pathlib import Path
from typing import Any
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout
)
from tts_cli.ui.components.slider_row import SliderRow
from tts_cli.ui.components.formats_widget import FormatsWidget

class TtsConfigWidget(QWidget):
    def __init__(self, values: dict[str, Any], batch: bool, main_window: Any, parent=None):
        super().__init__(parent)
        self.values = values
        self.batch = batch
        self.main_window = main_window
        
        self.form = QFormLayout(self)
        self.form.setContentsMargins(18, 24, 18, 24)
        self.form.setSpacing(12)
        
        self._build_form()

    def _build_form(self) -> None:
        engine = QComboBox()
        engine.addItems(["edge", "google"])
        engine.setCurrentText(str(self.values["engine"]))
        
        voice = QComboBox()
        voice.setEditable(True)
        voice.addItem(str(self.values["voice"]))
        voice.setCurrentText(str(self.values["voice"]))
        self.main_window.voice_combos.append((voice, self.values))
        
        rate_row = SliderRow(str(self.values["rate"]), -100, 100, "%")
        pitch_row = SliderRow(str(self.values["pitch"]), -50, 50, "Hz")
        volume_row = SliderRow(str(self.values["volume"]), -100, 100, "%")
        
        subtitle = QComboBox()
        subtitle.addItems(["phrase", "sentence", "word"])
        subtitle.setCurrentText(str(self.values["subtitle_mode"]))
        
        max_words = QSpinBox()
        max_words.setMinimum(1)
        max_words.setValue(int(self.values["max_words"]))
        
        output = QLineEdit(str(self.values["output"]))
        output.setCursorPosition(0)
        
        if not hasattr(self.main_window, "output_inputs"):
            self.main_window.output_inputs = []
        self.main_window.output_inputs.append((output, self.values))
        
        choose_output = QPushButton("Chọn thư mục")
        choose_output.clicked.connect(lambda: self._choose_output_folder(output))
        
        open_output = QPushButton("Mở")
        open_output.clicked.connect(lambda: self._open_output_folder(output))
        
        output_row = QWidget()
        output_layout = QVBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(6)
        output_layout.addWidget(output)
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(choose_output, 1)
        btn_layout.addWidget(open_output)
        output_layout.addLayout(btn_layout)
        
        formats = FormatsWidget(self.values)
        
        retries = QSpinBox()
        retries.setMinimum(0)
        retries.setValue(int(self.values["retries"]))
        
        timeout = QDoubleSpinBox()
        timeout.setMinimum(0.1)
        timeout.setValue(float(self.values["timeout"]))
        
        proxy = QLineEdit(str(self.values["proxy"] or ""))
        
        controls = [
            ("Engine", engine, "engine"),
            ("Voice", voice, "voice"),
            ("Rate", rate_row, "rate"),
            ("Pitch", pitch_row, "pitch"),
            ("Volume", volume_row, "volume"),
            ("Subtitle mode", subtitle, "subtitle_mode"),
            ("Max words", max_words, "max_words"),
            ("Output folder", output_row, "output"),
            ("Formats", formats, "formats"),
            ("Retries", retries, "retries"),
            ("Timeout", timeout, "timeout"),
            ("Proxy", proxy, "proxy")
        ]
        
        for label, control, key in controls:
            self.form.addRow(label, control)
            if isinstance(control, QComboBox):
                control.currentTextChanged.connect(lambda value, k=key: (
                    self.values.__setitem__(k, value),
                    self.main_window.state.save_to_file()
                ))
                if key == "engine":
                    control.currentTextChanged.connect(lambda value: self.main_window._load_voice_options(value))
            elif control is rate_row:
                rate_row.slider.valueChanged.connect(lambda value: (
                    self.values.__setitem__("rate", f"{value:+d}%"),
                    self.main_window.state.save_to_file()
                ))
            elif control is pitch_row:
                pitch_row.slider.valueChanged.connect(lambda value: (
                    self.values.__setitem__("pitch", f"{value:+d}Hz"),
                    self.main_window.state.save_to_file()
                ))
            elif control is volume_row:
                volume_row.slider.valueChanged.connect(lambda value: (
                    self.values.__setitem__("volume", f"{value:+d}%"),
                    self.main_window.state.save_to_file()
                ))
            elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
                control.valueChanged.connect(lambda value, k=key: (
                    self.values.__setitem__(k, value),
                    self.main_window.state.save_to_file()
                ))
            elif isinstance(control, QLineEdit):
                if key == "output":
                    output.textChanged.connect(lambda value: self._update_all_outputs(value))
                else:
                    control.textChanged.connect(lambda value, k=key: (
                        self.values.__setitem__(k, value),
                        self.main_window.state.save_to_file()
                    ))
                
        if self.batch:
            for label, key in [("Recursive", "recursive"), ("Skip existing", "skip_existing"), ("Continue on error", "continue_on_error"), ("Dry run", "dry_run")]:
                box = QPushButton(label)
                box.setCheckable(True)
                box.setChecked(bool(self.values[key]))
                box.toggled.connect(lambda checked, k=key: (
                    self.values.__setitem__(k, checked),
                    self.main_window.state.save_to_file()
                ))
                self.form.addRow(box)
                
        reset = QPushButton("Reset mặc định")
        reset.clicked.connect(self._reset_config)
        self.form.addRow(reset)

    def _update_all_outputs(self, path: str) -> None:
        """Đồng bộ đường dẫn output cho tất cả các view/tab và lưu state tự động"""
        self.values["output"] = path
        self.main_window.state.save_to_file()
        if hasattr(self.main_window, "output_inputs"):
            for line_edit, val_dict in self.main_window.output_inputs:
                val_dict["output"] = path
                if line_edit.text() != path:
                    line_edit.blockSignals(True)
                    line_edit.setText(path)
                    line_edit.setCursorPosition(0)
                    line_edit.blockSignals(False)

    def _choose_output_folder(self, output: QLineEdit) -> None:
        from PySide6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục output", output.text())
        if path:
            self._update_all_outputs(path)

    @staticmethod
    def _open_output_folder(output: QLineEdit) -> None:
        path = Path(output.text()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _reset_config(self) -> None:
        self.main_window._reset_tts_config(self.values, self.batch)