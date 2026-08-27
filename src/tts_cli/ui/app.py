"""PySide6 desktop application for the TTS use cases."""

import asyncio
import os
import sys
from uuid import uuid4
from types import SimpleNamespace
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QPlainTextEdit, QSlider, QSpinBox, QDoubleSpinBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from tts_cli.adapters.input.media import is_audio_file, is_video_file
from tts_cli.adapters.input.resolver import InputResolver
from tts_cli.adapters.subtitle.srt import cues_to_srt
from tts_cli.application.batch_process import BatchProcessUseCase
from tts_cli.application.bus import CommandBus, EventBus, EventProgress, ExecuteOperation
from tts_cli.application.composition import (
    create_batch_dependencies,
    create_synthesis,
    create_transcription,
    create_voice_catalog,
)
from tts_cli.application.transcribe import TranscribeUseCase
from tts_cli.cli.constants import VERSION
from tts_cli.core.models import TTSConfig, TranscribeConfig
from tts_cli.ui.state import AppState
from tts_cli.core.events import OperationCompleted, OperationFailed, ProgressUpdated


class TaskWorker(QObject):
    completed = Signal(object, object)
    finished = Signal()

    def __init__(self, operation: Callable[[], Any]):
        super().__init__()
        self.operation = operation
        self.result: Any = None
        self.error: Exception | None = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.task: asyncio.Task[Any] | None = None

    @Slot()
    def run(self) -> None:
        result: Any = None
        error: Exception | None = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.task = self.loop.create_task(self.operation())
            result = self.loop.run_until_complete(self.task)
        except asyncio.CancelledError:
            error = RuntimeError("Tác vụ đã bị hủy.")
        except Exception as caught:
            error = caught
        finally:
            self.loop.close()
            self.loop = None
            self.task = None
        self.result = result
        self.error = error
        self.completed.emit(result, error)
        self.finished.emit()

    def cancel(self) -> None:
        if self.loop is not None and self.task is not None:
            self.loop.call_soon_threadsafe(self.task.cancel)


class MainWindow(QMainWindow):
    progress_changed = Signal(int, str)
    operation_completed = Signal(object, object)
    voice_catalog_loaded = Signal(str, object, object)

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self.event_bus = EventBus()
        self.command_bus = CommandBus(self.event_bus)
        self.operation_id: str | None = None
        self.operation_running = False
        self.close_after_cancel = False
        self.worker_thread: QThread | None = None
        self.worker: TaskWorker | None = None
        self.operation_controls: list[QWidget] = []
        self.voice_combos: list[tuple[QComboBox, dict[str, Any]]] = []
        self.voice_load_thread: QThread | None = None
        self.voice_load_worker: TaskWorker | None = None
        self.voice_load_engine: str | None = None
        self.voice_requested_engine: str | None = None
        self.setWindowTitle("Edge TTS CLI")
        self.resize(1100, 700)
        self._center_on_screen()
        self.progress_changed.connect(self._update_progress)
        self.event_bus.subscribe(ProgressUpdated, self._on_progress_event)
        self.event_bus.subscribe(OperationCompleted, self._on_completed_event)
        self.event_bus.subscribe(OperationFailed, self._on_failed_event)
        self.operation_completed.connect(self._operation_completed)
        self.voice_catalog_loaded.connect(self._apply_voice_options)
        self._build_ui()
        QTimer.singleShot(0, lambda: self._load_voice_options("edge"))

    def _center_on_screen(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        self.title = QLabel("Edge TTS CLI")
        self.title.setObjectName("title")
        self.mode_label = QLabel("Generate")
        self.mode_label.setObjectName("mode_label")
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("status_label")
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.mode_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        root_layout.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.navigation = QListWidget()
        self.navigation.addItems(["Generate", "Batch", "Transcribe", "Voices"])
        self.navigation.setFixedWidth(190)
        self.navigation.setSpacing(4)
        self.navigation.setUniformItemSizes(True)
        self.navigation.currentRowChanged.connect(self._change_mode)
        body.addWidget(self.navigation)
        self.content = QStackedWidget()
        self.content.addWidget(self._generate_page())
        self.content.addWidget(self._batch_page())
        self.content.addWidget(self._transcribe_page())
        self.content.addWidget(self._voices_page())
        body.addWidget(self.content, 1)
        self.configuration = QStackedWidget()
        self.configuration.setFixedWidth(330)
        self.configuration.addWidget(self._tts_config(self.state.generate_values, False))
        self.configuration.addWidget(self._tts_config(self.state.batch_values, True))
        self.configuration.addWidget(self._transcribe_config())
        self.configuration.addWidget(self._voices_config())
        body.addWidget(self.configuration)
        root_layout.addLayout(body, 1)

        footer = QFrame()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        self.progress_label = QLabel("0% - Sẵn sàng")
        self.progress_label.setObjectName("progress_label")
        self.progress_label.setMinimumWidth(180)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.result_label = QLabel("Chưa có kết quả")
        self.result_label.setObjectName("result_label")
        self.result_label.setMinimumWidth(150)
        self.result_label.setMaximumWidth(220)
        version_label = QLabel(f"Version: {VERSION}")
        version_label.setObjectName("version_label")
        version_label.setMinimumWidth(78)
        footer_layout.addWidget(self.progress_label, 1)
        footer_layout.addWidget(self.result_label)
        footer_layout.addWidget(version_label)
        root_layout.addWidget(footer)
        self.setCentralWidget(root)
        self.operation_controls.extend([
            self.navigation,
            self.text_editor,
            self.batch_directory,
            self.media_path,
            self.transcribe_output,
            self.voice_table,
            *self.configuration.findChildren(QWidget),
        ])
        self.navigation.setCurrentRow(0)

    def _page(self, title: str, description: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)
        heading = QLabel(title)
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel(description))
        return page, layout

    def _generate_page(self) -> QWidget:
        page, layout = self._page("Generate audio", "Nhập văn bản hoặc chọn một file TXT, SRT, VTT.")
        self.text_editor = QPlainTextEdit()
        self.text_editor.setPlaceholderText("Text trực tiếp")
        self.text_editor.setMinimumHeight(300)
        layout.addWidget(self.text_editor)
        file_row = QHBoxLayout()
        self.file_label = QLabel("Chưa chọn file")
        choose = QPushButton("Chọn file")
        choose.clicked.connect(self._choose_input_file)
        self.operation_controls.append(choose)
        file_row.addWidget(self.file_label, 1)
        file_row.addWidget(choose)
        layout.addLayout(file_row)
        generate = QPushButton("Generate")
        generate.clicked.connect(self._run_generate)
        self.operation_controls.append(generate)
        layout.addWidget(generate)
        layout.addStretch()
        return page

    def _batch_page(self) -> QWidget:
        page, layout = self._page("Batch processing", "Xử lý file TXT, SRT hoặc VTT theo thứ tự.")
        self.batch_directory = QLineEdit()
        self.batch_directory.setPlaceholderText("Thư mục nguồn")
        choose = QPushButton("Chọn thư mục")
        choose.clicked.connect(self._choose_batch_directory)
        self.operation_controls.append(choose)
        row = QHBoxLayout()
        row.addWidget(self.batch_directory, 1)
        row.addWidget(choose)
        layout.addLayout(row)
        start = QPushButton("Start batch")
        start.clicked.connect(self._run_batch)
        self.operation_controls.append(start)
        layout.addWidget(start)
        layout.addStretch()
        return page

    def _transcribe_page(self) -> QWidget:
        page, layout = self._page("Transcribe media", "Tạo file SRT từ audio hoặc video bằng Whisper local.")
        self.media_path = QLineEdit()
        self.media_path.setPlaceholderText("File audio/video")
        choose = QPushButton("Chọn media")
        choose.clicked.connect(self._choose_media)
        self.operation_controls.append(choose)
        row = QHBoxLayout()
        row.addWidget(self.media_path, 1)
        row.addWidget(choose)
        layout.addLayout(row)
        self.transcribe_output = QLineEdit("subtitle.srt")
        layout.addWidget(self.transcribe_output)
        run = QPushButton("Transcribe")
        run.clicked.connect(self._run_transcribe)
        self.operation_controls.append(run)
        layout.addWidget(run)
        layout.addStretch()
        return page

    def _voices_page(self) -> QWidget:
        page, layout = self._page("Voice catalog", "Tìm voice theo engine, locale, giới tính hoặc tên.")
        run = QPushButton("Load voices")
        run.clicked.connect(self._run_voices)
        self.operation_controls.append(run)
        layout.addWidget(run)
        self.voice_table = QPlainTextEdit()
        self.voice_table.setReadOnly(True)
        layout.addWidget(self.voice_table, 1)
        return page

    def _form(self) -> tuple[QWidget, QFormLayout]:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(18, 24, 18, 24)
        form.setSpacing(12)
        return widget, form

    def _tts_config(self, values: dict[str, Any], batch: bool) -> QWidget:
        widget, form = self._form()
        engine = QComboBox(); engine.addItems(["edge", "google"]); engine.setCurrentText(values["engine"])
        voice = QComboBox(); voice.setEditable(True); voice.addItem(str(values["voice"])); voice.setCurrentText(str(values["voice"]))
        self.voice_combos.append((voice, values))
        rate_widget, rate_slider, rate_value = self._tts_slider(str(values["rate"]), -100, 100, "%")
        pitch_widget, pitch_slider, pitch_value = self._tts_slider(str(values["pitch"]), -50, 50, "Hz")
        volume_widget, volume_slider, volume_value = self._tts_slider(str(values["volume"]), -100, 100, "%")
        subtitle = QComboBox(); subtitle.addItems(["phrase", "sentence", "word"]); subtitle.setCurrentText(values["subtitle_mode"])
        max_words = QSpinBox(); max_words.setMinimum(1); max_words.setValue(values["max_words"])
        output = QLineEdit(str(values["output"]))
        choose_output = QPushButton("Chọn")
        choose_output.clicked.connect(lambda: self._choose_output_folder(output, values))
        open_output = QPushButton("Mở")
        open_output.clicked.connect(lambda: self._open_output_folder(output))
        output_row = QWidget(); output_layout = QHBoxLayout(output_row); output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(output, 1); output_layout.addWidget(choose_output); output_layout.addWidget(open_output)
        formats = self._formats_widget(values)
        retries = QSpinBox(); retries.setMinimum(0); retries.setValue(values["retries"])
        timeout = QDoubleSpinBox(); timeout.setMinimum(0.1); timeout.setValue(values["timeout"])
        proxy = QLineEdit(str(values["proxy"] or ""))
        controls: list[tuple[str, QWidget, str]] = [("Engine", engine, "engine"), ("Voice", voice, "voice"), ("Rate", rate_widget, "rate"), ("Pitch", pitch_widget, "pitch"), ("Volume", volume_widget, "volume"), ("Subtitle mode", subtitle, "subtitle_mode"), ("Max words", max_words, "max_words"), ("Output folder", output_row, "output"), ("Formats", formats, "formats"), ("Retries", retries, "retries"), ("Timeout", timeout, "timeout"), ("Proxy", proxy, "proxy")]
        for label, control, key in controls:
            form.addRow(label, control)
            if isinstance(control, QComboBox):
                control.currentTextChanged.connect(lambda value, key=key: values.__setitem__(key, value))
                if key == "engine":
                    control.currentTextChanged.connect(lambda value: self._load_voice_options(value))
            elif control is rate_widget:
                rate_slider.valueChanged.connect(lambda value: values.__setitem__("rate", f"{value:+d}%"))
                rate_slider.valueChanged.connect(lambda value: rate_value.setText(f"{value:+d}%"))
            elif control is pitch_widget:
                pitch_slider.valueChanged.connect(lambda value: values.__setitem__("pitch", f"{value:+d}Hz"))
                pitch_slider.valueChanged.connect(lambda value: pitch_value.setText(f"{value:+d}Hz"))
            elif control is volume_widget:
                volume_slider.valueChanged.connect(lambda value: values.__setitem__("volume", f"{value:+d}%"))
                volume_slider.valueChanged.connect(lambda value: volume_value.setText(f"{value:+d}%"))
            elif isinstance(control, (QSpinBox, QDoubleSpinBox)): control.valueChanged.connect(lambda value, key=key: values.__setitem__(key, value))
            elif isinstance(control, QLineEdit): control.textChanged.connect(lambda value, key=key: values.__setitem__(key, value))
        if batch:
            for label, key in [("Recursive", "recursive"), ("Skip existing", "skip_existing"), ("Continue on error", "continue_on_error"), ("Dry run", "dry_run")]:
                box = QPushButton(label); box.setCheckable(True); box.setChecked(values[key]); box.toggled.connect(lambda checked, key=key: values.__setitem__(key, checked)); form.addRow(box)
        reset = QPushButton("Reset mặc định")
        reset.clicked.connect(lambda: self._reset_tts_config(values, batch))
        form.addRow(reset)
        return widget

    def _reset_tts_config(self, values: dict[str, Any], batch: bool) -> None:
        defaults = AppState().batch_values if batch else AppState().generate_values
        self.voice_combos = [(combo, state) for combo, state in self.voice_combos if state is not values]
        values.clear()
        values.update(defaults)
        index = 1 if batch else 0
        old_widget = self.configuration.widget(index)
        new_widget = self._tts_config(values, batch)
        if old_widget is not None:
            self.configuration.removeWidget(old_widget)
            old_widget.deleteLater()
        self.configuration.insertWidget(index, new_widget)
        self.configuration.setCurrentIndex(index)

    @staticmethod
    def _formats_widget(values: dict[str, Any]) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        selected = {item.strip().lower() for item in str(values["formats"]).split(",") if item.strip()}
        checkboxes: list[QCheckBox] = []
        for format_name in ("mp3", "srt", "vtt", "json"):
            checkbox = QCheckBox(format_name.upper())
            checkbox.setChecked(format_name in selected)
            checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        def update_formats() -> None:
            active = [checkbox.text().lower() for checkbox in checkboxes if checkbox.isChecked()]
            if not active:
                checkboxes[0].setChecked(True)
                active = [checkboxes[0].text().lower()]
            values["formats"] = ",".join(active)

        for checkbox in checkboxes:
            checkbox.toggled.connect(update_formats)
        return container

    def _load_voice_options(self, engine: str) -> None:
        self.voice_requested_engine = str(engine)
        if self.voice_load_thread is not None:
            return
        self.voice_load_engine = self.voice_requested_engine

        async def operation() -> list[dict[str, Any]]:
            return await create_voice_catalog(self.voice_load_engine or "edge").find()

        self.voice_load_thread = QThread(self)
        self.voice_load_worker = TaskWorker(operation)
        self.voice_load_worker.moveToThread(self.voice_load_thread)
        self.voice_load_thread.started.connect(self.voice_load_worker.run)
        self.voice_load_worker.completed.connect(
            lambda result, error: self.voice_catalog_loaded.emit(
                self.voice_load_engine or "edge", result, error
            )
        )
        self.voice_load_worker.completed.connect(self.voice_load_worker.deleteLater)
        self.voice_load_worker.finished.connect(self.voice_load_thread.quit)
        thread = self.voice_load_thread
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._voice_load_finished)
        thread.start()

    @Slot(str, object, object)
    def _apply_voice_options(self, engine: str, result: Any, error: Exception | None) -> None:
        if error is not None:
            if engine == "google":
                self.status_label.setText(
                    "Google voice catalog cần GOOGLE_APPLICATION_CREDENTIALS"
                )
            else:
                self.status_label.setText(f"Voice catalog lỗi: {error}")
            return
        names = [str(item.get("ShortName", "")) for item in result if item.get("ShortName")]
        if not names:
            self.status_label.setText("Voice catalog không có voice")
            return
        for voice, values in self.voice_combos:
            if str(values["engine"]) != engine:
                continue
            current = str(values["voice"])
            voice.blockSignals(True)
            voice.clear()
            voice.addItems(names)
            voice.setCurrentText(current if current in names else names[0])
            voice.blockSignals(False)
            values["voice"] = voice.currentText()
        if self.state.status == "Idle":
            self.status_label.setText("Idle")

    @Slot()
    def _voice_load_finished(self) -> None:
        self.voice_load_worker = None
        self.voice_load_thread = None
        if self.voice_requested_engine != self.voice_load_engine:
            self._load_voice_options(self.voice_requested_engine or "edge")

    @staticmethod
    def _tts_slider(value: str, minimum: int, maximum: int, suffix: str) -> tuple[QWidget, QSlider, QLabel]:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        try:
            numeric = int(value.replace("%", "").replace("Hz", ""))
        except ValueError:
            numeric = 0
        slider.setValue(max(minimum, min(maximum, numeric)))
        display = QLabel(f"{slider.value():+d}{suffix}")
        display.setMinimumWidth(48)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(slider, 1)
        layout.addWidget(display)
        return row, slider, display

    def _choose_output_folder(self, output: QLineEdit, values: dict[str, Any]) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục output", output.text())
        if path:
            output.setText(path)
            values["output"] = path

    @staticmethod
    def _open_output_folder(output: QLineEdit) -> None:
        path = Path(output.text()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(str(path))

    def _transcribe_config(self) -> QWidget:
        widget, form = self._form()
        model = QComboBox(); model.addItems(["tiny", "base", "small", "medium", "large-v3"])
        device = QComboBox(); device.addItems(["auto", "cpu", "cuda"])
        language = QLineEdit()
        controls: list[tuple[str, QComboBox | QLineEdit, str]] = [("Model size", model, "model_size"), ("Device", device, "device"), ("Language", language, "language")]
        for label, control, key in controls:
            form.addRow(label, control)
            signal = control.currentTextChanged if isinstance(control, QComboBox) else control.textChanged
            signal.connect(lambda value, key=key: self.state.transcribe_values.__setitem__(key, value))
        return widget

    def _voices_config(self) -> QWidget:
        widget, form = self._form()
        controls: list[tuple[str, QComboBox | QLineEdit, str]] = [("Engine", QComboBox(), "engine"), ("Language", QLineEdit(), "language"), ("Gender", QComboBox(), "gender"), ("Search", QLineEdit(), "search")]
        for label, control, key in controls:
            if isinstance(control, QComboBox): control.addItems(["edge", "google"] if key == "engine" else ["", "Male", "Female"])
            form.addRow(label, control)
            signal = control.currentTextChanged if isinstance(control, QComboBox) else control.textChanged
            signal.connect(lambda value, key=key: self.state.voices_values.__setitem__(key, value))
        return widget

    def _change_mode(self, index: int) -> None:
        self.content.setCurrentIndex(index)
        self.configuration.setCurrentIndex(index)
        self.mode_label.setText(self.navigation.currentItem().text())

    def _choose_input_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn input", "", "Text/subtitle (*.txt *.srt *.vtt)")
        if path:
            self.state.generate_values["file"] = path
            self.text_editor.clear()
            self.file_label.setText(Path(path).name)

    def _choose_batch_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục nguồn")
        if path:
            self.batch_directory.setText(path)
            self.state.batch_values["directory"] = path

    def _choose_media(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn media", "", "Media files (*)")
        if path:
            self.media_path.setText(path)
            self.state.transcribe_values["source"] = path

    def _proxy_value(self, values: dict[str, Any]) -> str | None:
        proxy = str(values["proxy"] or "").strip()
        if not proxy:
            return None
        parsed = urlparse(proxy)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Proxy phải có dạng http://host:port hoặc https://host:port.")
        return proxy

    def _start(self, operation: Callable[[], Any]) -> None:
        if self.operation_running:
            return
        self.state.start()
        self.operation_running = True
        self._set_operation_controls(False)
        self.operation_id = str(uuid4())
        self.status_label.setText("Running")
        self.progress_label.setText("0% - Đang xử lý...")
        self.result_label.setText("Đang xử lý...")
        self.worker_thread = QThread(self)
        self.worker = TaskWorker(lambda: self.command_bus.dispatch(ExecuteOperation(operation, self.operation_id)))
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.completed.connect(self.worker.deleteLater)
        thread = self.worker_thread
        self.worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._thread_finished)
        self.worker_thread.start()

    @Slot()
    def _thread_finished(self) -> None:
        self.operation_running = False
        self.worker = None
        self.worker_thread = None
        self._set_operation_controls(True)
        if self.close_after_cancel:
            self.close_after_cancel = False
            self.close()

    def _cancel_operation(self) -> None:
        if self.worker is not None:
            self.close_after_cancel = True
            self.status_label.setText("Cancelling")
            self.result_label.setText("Đang hủy tác vụ...")
            self.worker.cancel()

    def _set_operation_controls(self, enabled: bool) -> None:
        live_controls: list[QWidget] = []
        for control in self.operation_controls:
            try:
                control.setEnabled(enabled)
            except RuntimeError:
                continue
            live_controls.append(control)
        self.operation_controls = live_controls

    def _on_progress_event(self, event: ProgressUpdated) -> None:
        if event.operation_id == self.operation_id:
            self.progress_changed.emit(event.current * 100 // event.total, event.stage)

    def _on_completed_event(self, event: OperationCompleted) -> None:
        if event.operation_id == self.operation_id:
            self.operation_completed.emit(event.result, None)

    def _on_failed_event(self, event: OperationFailed) -> None:
        if event.operation_id == self.operation_id:
            self.operation_completed.emit(None, event.error)

    @Slot(object, object)
    def _operation_completed(self, result: Any, error: Exception | None) -> None:
        if self.state.status != "Running":
            return
        if error is not None:
            if self.close_after_cancel:
                self.state.fail(error)
                self.progress_label.setText("0% - Đã hủy")
                self.status_label.setText("Cancelled")
                self.result_label.setText("Tác vụ đã hủy")
            else:
                self._failure(error)
        else:
            self._success(result)
        if self.worker_thread is not None:
            self.worker_thread.quit()

    @Slot(int, str)
    def _update_progress(self, percent: int, detail: str) -> None:
        if self.state.status != "Running":
            return
        self.progress_label.setText(f"{percent}% - {detail}")
        self.result_label.setText(detail)

    def _run_generate(self) -> None:
        values = self.state.generate_values
        text = self.text_editor.toPlainText()
        if bool(text) == bool(values["file"]):
            QMessageBox.warning(self, "Input", "Hãy chọn đúng một nguồn.")
            return
        values["text"] = text

        async def operation() -> int:
            args = SimpleNamespace(text=values["text"] or None, file=values["file"] or None)
            config = TTSConfig(str(values["voice"]).strip(), str(values["rate"]), str(values["pitch"]), str(values["volume"]), int(values["retries"]), float(values["timeout"]), self._proxy_value(values))
            input_text = InputResolver().resolve(args).text
            return await create_synthesis(config, str(values["engine"]), event_bus=self.event_bus, operation_id=self.operation_id).execute(input_text, Path(str(values["output"])), str(values["subtitle_mode"]), int(values["max_words"]), formats=str(values["formats"]))
        self._start(operation)

    def _run_batch(self) -> None:
        values = self.state.batch_values

        async def operation() -> None:
            config = TTSConfig(str(values["voice"]).strip(), str(values["rate"]), str(values["pitch"]), str(values["volume"]), int(values["retries"]), float(values["timeout"]), self._proxy_value(values))
            progress_factory = lambda total, label: EventProgress(total, label, self.event_bus, self.operation_id or "")
            batch_files, input_resolver, output_resolver, progress = create_batch_dependencies(progress_factory)
            await BatchProcessUseCase(create_synthesis(config, str(values["engine"]), event_bus=self.event_bus, operation_id=self.operation_id), batch_files, input_resolver, output_resolver, progress).execute(Path(str(values["directory"])), Path(str(values["output"])), bool(values["recursive"]), str(values["subtitle_mode"]), int(values["max_words"]), 1, bool(values["skip_existing"]), bool(values["continue_on_error"]), bool(values["dry_run"]), str(values["formats"]))
        self._start(operation)

    def _run_transcribe(self) -> None:
        source = Path(self.media_path.text())
        if not source.is_file() or (not is_audio_file(source) and not is_video_file(source)):
            QMessageBox.warning(self, "Media", "File audio/video không hợp lệ.")
            return
        values = self.state.transcribe_values

        async def operation() -> Any:
            transcriber = await create_transcription(TranscribeConfig(str(values["model_size"]), str(values["language"]) or None, str(values["device"])))
            return await TranscribeUseCase(transcriber, cues_to_srt).execute(source, Path(self.transcribe_output.text()))
        self._start(operation)

    def _run_voices(self) -> None:
        values = self.state.voices_values

        async def operation() -> Any:
            return await create_voice_catalog(str(values["engine"])).find(str(values["language"]) or None, str(values["gender"]) or None, str(values["search"]) or None)
        self._start(operation)

    @Slot(object)
    def _success(self, result: Any) -> None:
        message = f"Tìm thấy {len(result)} voice" if isinstance(result, list) else "Tác vụ đã hoàn tất"
        self.state.succeed(message, result)
        self.progress_label.setText("100% - Hoàn tất")
        self.status_label.setText("Succeeded")
        self.result_label.setText(message)
        if isinstance(result, list):
            self.voice_table.setPlainText("\n".join(f"{item.get('ShortName', '')} | {item.get('Locale', '')} | {item.get('Gender', '')}" for item in result))

    @Slot(Exception)
    def _failure(self, error: Exception) -> None:
        self.progress_label.setText("0% - Thất bại")
        self.status_label.setText("Failed")
        self.state.fail(error)
        self.result_label.setText(self.state.error_message or "Tác vụ thất bại")
        QMessageBox.critical(self, "Tác vụ thất bại", self.state.error_message or str(error))

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.operation_running:
            answer = QMessageBox.question(
                self, "Đang xử lý", "Tác vụ đang chạy. Hủy và đóng ứng dụng?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._cancel_operation()
            event.ignore()
            return
        event.accept()


def main() -> int:
    existing_app = QApplication.instance()
    app = existing_app if isinstance(existing_app, QApplication) else QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background: #f4f7fb; }
        #header, #footer { background: #0b1220; }
        #header QLabel, #footer QLabel { color: #ffffff; }
        #header { padding: 8px; }
        #footer { padding: 4px; }
        #title { font-size: 18px; font-weight: 700; }
        #mode_label, #status_label, #progress_label, #result_label, #version_label {
            color: #ffffff;
        }
        QListWidget { background: white; border: 0; padding: 18px 12px; }
        QListWidget::item { min-height: 38px; padding: 0 12px; margin: 2px 0; }
        QListWidget::item:selected { background: #dcecff; color: #185ea8; }
        #heading { font-size: 24px; font-weight: 700; }
    """)
    window = MainWindow()
    window.showMinimized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
