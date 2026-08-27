import sys
from PySide6.QtWidgets import QApplication
from tts_cli.ui.windows.main_window import MainWindow

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
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())