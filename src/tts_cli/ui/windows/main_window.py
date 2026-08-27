import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable
from urllib.parse import urlparse
from uuid import uuid4

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
    QStackedWidget, QVBoxLayout, QWidget, QSpinBox, QDoubleSpinBox, QPushButton
)

from tts_cli.adapters.input.media import is_audio_file, is_video_file
from tts_cli.adapters.input.processor import normalize_text
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

from tts_cli.ui.views.generate_view import GenerateView
from tts_cli.ui.views.batch_view import BatchView
from tts_cli.ui.views.transcribe_view import TranscribeView
from tts_cli.ui.views.voices_view import VoicesView
from tts_cli.ui.components.tts_config_widget import TtsConfigWidget


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

        self.state = AppState.load_from_file()
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
        
        self.text_editor = None
        self.batch_directory = None
        self.media_path = None
        self.transcribe_output = None
        self.voice_table = None

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
        self.generate_view = GenerateView(self)
        self.batch_view = BatchView(self)
        self.transcribe_view = TranscribeView(self)
        self.voices_view = VoicesView(self)
        
        self.content.addWidget(self.generate_view)
        self.content.addWidget(self.batch_view)
        self.content.addWidget(self.transcribe_view)
        self.content.addWidget(self.voices_view)
        body.addWidget(self.content, 1)

        self.configuration = QStackedWidget()
        self.configuration.setFixedWidth(330)
        self.configuration.addWidget(TtsConfigWidget(self.state.generate_values, False, self))
        self.configuration.addWidget(TtsConfigWidget(self.state.batch_values, True, self))
        
        transcribe_config_widget = QWidget()
        tc_form = QFormLayout(transcribe_config_widget)
        tc_form.setContentsMargins(18, 24, 18, 24)
        tc_form.setSpacing(12)
        model = QComboBox(); model.addItems(["tiny", "base", "small", "medium", "large-v3"])
        device = QComboBox(); device.addItems(["auto", "cpu", "cuda"])
        language = QLineEdit()
        for label, control, key in [("Model size", model, "model_size"), ("Device", device, "device"), ("Language", language, "language")]:
            tc_form.addRow(label, control)
            signal = control.currentTextChanged if isinstance(control, QComboBox) else control.textChanged
            signal.connect(lambda value, k=key: (
                self.state.transcribe_values.__setitem__(k, value),
                self.state.save_to_file(),
            ))
        self.configuration.addWidget(transcribe_config_widget)

        voices_config_widget = QWidget()
        vc_form = QFormLayout(voices_config_widget)
        vc_form.setContentsMargins(18, 24, 18, 24)
        vc_form.setSpacing(12)
        for label, control, key in [("Engine", QComboBox(), "engine"), ("Language", QLineEdit(), "language"), ("Gender", QComboBox(), "gender"), ("Search", QLineEdit(), "search")]:
            if isinstance(control, QComboBox): 
                control.addItems(["edge", "google"] if key == "engine" else ["", "Male", "Female"])
            vc_form.addRow(label, control)
            signal = control.currentTextChanged if isinstance(control, QComboBox) else control.textChanged
            signal.connect(lambda value, k=key: (
                self.state.voices_values.__setitem__(k, value),
                self.state.save_to_file(),
            ))
        self.configuration.addWidget(voices_config_widget)

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
            *self.configuration.findChildren(QWidget),
        ])
        self.navigation.setCurrentRow(0)

    def _change_mode(self, index: int) -> None:
        self.content.setCurrentIndex(index)
        self.configuration.setCurrentIndex(index)
        self.mode_label.setText(self.navigation.currentItem().text())

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
            if isinstance(error, RuntimeError) and "bị hủy" in str(error):
                self.state.fail(error)
                self.progress_label.setText("0% - Đã hủy")
                self.status_label.setText("Cancelled")
                self.result_label.setText("Tác vụ đã hủy")
            elif self.close_after_cancel:
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
        text = normalize_text(self.generate_view.text_editor.toPlainText())
        input_file = str(values["file"] or "")
        if bool(text) == bool(input_file):
            QMessageBox.warning(self, "Input", "Hãy chọn đúng một nguồn.")
            return
        input_args = SimpleNamespace(text=text or None, file=input_file or None)
        resolved_text = InputResolver().resolve(input_args).text
        values["text"] = resolved_text if not input_file else ""
        input_text = resolved_text
        voice = str(values["voice"])
        rate = str(values["rate"])
        pitch = str(values["pitch"])
        volume = str(values["volume"])
        retries = int(values["retries"])
        timeout = float(values["timeout"])
        proxy = self._proxy_value(values)
        engine = str(values["engine"])
        output = Path(str(values["output"]))
        subtitle_mode = str(values["subtitle_mode"])
        max_words = int(values["max_words"])
        formats = str(values["formats"])
        operation_id = self.operation_id

        async def operation() -> int:
            config = TTSConfig(voice.strip(), rate, pitch, volume, retries, timeout, proxy)
            return await create_synthesis(config, engine, event_bus=self.event_bus, operation_id=operation_id).execute(input_text, output, subtitle_mode, max_words, formats=formats)
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
        source = Path(self.transcribe_view.media_path.text())
        if not source.is_file() or (not is_audio_file(source) and not is_video_file(source)):
            QMessageBox.warning(self, "Media", "File audio/video không hợp lệ.")
            return
        values = self.state.transcribe_values

        async def operation() -> Any:
            transcriber = await create_transcription(TranscribeConfig(str(values["model_size"]), str(values["language"]) or None, str(values["device"])))
            return await TranscribeUseCase(transcriber, cues_to_srt).execute(source, Path(self.transcribe_view.transcribe_output.text()))
        self._start(operation)

    def _run_voices(self) -> None:
        values = self.state.voices_values

        async def operation() -> Any:
            return await create_voice_catalog(str(values["engine"])).find(str(values["language"]) or None, str(values["gender"]) or None, str(values["search"]) or None)
        self._start(operation)

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

    def _reset_tts_config(self, values: dict[str, Any], batch: bool) -> None:
        defaults = AppState().batch_values if batch else AppState().generate_values
        self.voice_combos = [(combo, state) for combo, state in self.voice_combos if state is not values]
        if hasattr(self, "output_inputs"):
            self.output_inputs = [
                (line_edit, state)
                for line_edit, state in self.output_inputs
                if state is not values
            ]
        values.clear()
        values.update(defaults)
        self.state.save_to_file()
        index = 1 if batch else 0
        old_widget = self.configuration.widget(index)
        old_control_ids = {id(control) for control in old_widget.findChildren(QWidget)} if old_widget is not None else set()
        new_widget = TtsConfigWidget(values, batch, self)
        if old_widget is not None:
            self.configuration.removeWidget(old_widget)
            old_widget.deleteLater()
        self.configuration.insertWidget(index, new_widget)
        self.configuration.setCurrentIndex(index)

        self.operation_controls = [
            ctrl for ctrl in self.operation_controls 
            if not isinstance(ctrl, (QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton)) 
            or id(ctrl) not in old_control_ids
        ]
        self.operation_controls.extend(new_widget.findChildren(QWidget))

    @Slot(object)
    def _success(self, result: Any) -> None:
        message = f"Tìm thấy {len(result)} voice" if isinstance(result, list) else "Tác vụ đã hoàn tất"
        self.state.succeed(message, result)
        self.progress_label.setText("100% - Hoàn tất")
        self.status_label.setText("Succeeded")
        self.result_label.setText(message)
        if isinstance(result, list) and self.voices_view.voice_table is not None:
            self.voices_view.voice_table.setPlainText("\n".join(f"{item.get('ShortName', '')} | {item.get('Locale', '')} | {item.get('Gender', '')}" for item in result))

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