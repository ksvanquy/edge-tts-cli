from typing import Any
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox

class FormatsWidget(QWidget):
    def __init__(self, values: dict[str, Any], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        selected = {item.strip().lower() for item in str(values["formats"]).split(",") if item.strip()}
        self.checkboxes: list[QCheckBox] = []
        for format_name in ("mp3", "srt", "vtt", "json"):
            checkbox = QCheckBox(format_name.upper())
            checkbox.setChecked(format_name in selected)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        def update_formats() -> None:
            active = [checkbox.text().lower() for checkbox in self.checkboxes if checkbox.isChecked()]
            if not active:
                self.checkboxes[0].setChecked(True)
                active = [self.checkboxes[0].text().lower()]
            values["formats"] = ",".join(active)

        for checkbox in self.checkboxes:
            checkbox.toggled.connect(update_formats)