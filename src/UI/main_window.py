from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from src.UI.login_page import LoginWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FDV App")
        self.setGeometry(100, 100, 640, 480)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        central_layout = QVBoxLayout(central_widget)

        # Create a spacer item for top and bottom
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add top spacer to the layout
        central_layout.addItem(top_spacer)

        # Create the frame for the login form without visible borders
        self.login_frame = QFrame()
        self.login_frame.setFrameShape(QFrame.NoFrame)
        self.login_frame.setFixedSize(300, 200)

        login_layout = QVBoxLayout(self.login_frame)
        login_layout.addWidget(LoginWidget())

        central_layout.addWidget(self.login_frame, 0, Qt.AlignCenter)

        # Add bottom spacer to the layout
        central_layout.addItem(bottom_spacer)

        self.show()
