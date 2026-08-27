from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QSlider, QLabel, QHBoxLayout

class SliderRow(QWidget):
    def __init__(self, value: str, minimum: int, maximum: int, suffix: str, parent=None):
        super().__init__(parent)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        try:
            numeric = int(value.replace("%", "").replace("Hz", ""))
        except ValueError:
            numeric = 0
        self.slider.setValue(max(minimum, min(maximum, numeric)))
        
        self.display = QLabel(f"{self.slider.value():+d}{suffix}")
        self.display.setMinimumWidth(48)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.display)
        
        self.slider.valueChanged.connect(lambda v: self.display.setText(f"{v:+d}{suffix}"))