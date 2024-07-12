from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient
from PySide6.QtWidgets import QPushButton, QGraphicsOpacityEffect


class ModernButton(QPushButton):
    def __init__(self, text, color_start, color_end, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(150, 40)  # Increased size for better visibility
        self._opacity = 0
        self.color_start = color_start
        self.color_end = color_end
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1)
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.2, QColor(self.color_start))
        gradient.setColorAt(1, QColor(self.color_end))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)  # Remove the border

        # Default radius if not specified in stylesheet
        radius = 10

        # Try to get the border-radius from the stylesheet
        style = self.styleSheet()
        if "border-radius:" in style:
            try:
                radius_str = style.split("border-radius:")[1].split(";")[0].strip()
                if radius_str.endswith("px"):
                    radius = int(radius_str[:-2])
                else:
                    radius = int(radius_str)
            except (IndexError, ValueError):
                pass  # Use default radius if parsing fails

        painter.drawRoundedRect(self.rect(), radius, radius)

        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

        if self._opacity > 0:
            painter.setOpacity(self._opacity)
            arrow_rect = self.rect().adjusted(self.width() - 50, 0, 0, 0)
            painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignCenter, "→")

    def enterEvent(self, event):
        self.animation.setDirection(QPropertyAnimation.Direction.Forward)
        self.animation.start()

    def leaveEvent(self, event):
        self.animation.setDirection(QPropertyAnimation.Direction.Backward)
        self.animation.start()

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity = Property(float, get_opacity, set_opacity)
