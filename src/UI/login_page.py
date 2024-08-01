from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSizePolicy,
    QFrame,
    QSpacerItem,
)

from src.logger.logger import Logger


def validate_credentials(username: str, password: str) -> str:
    """
    Validates the entered username and password.

    Args:
        username (str): The entered username.
        password (str): The entered password.

    Returns:
        str: An error message if validation fails, otherwise an empty string.
    """
    if not username.strip() and not password.strip():
        return "Username and Password cannot be empty."
    elif not username.strip():
        return "Username cannot be empty."
    elif not password.strip():
        return "Password cannot be empty."
    else:
        return ""


class LoginPage(QWidget):
    navigate_to_site_details = Signal()
    login_successful = Signal()

    def __init__(self, backend) -> None:
        """
        Initializes the LoginPage with UI components and backend integration.
        """
        super().__init__()

        self.error_label = QLabel("")
        self.password_input = QLineEdit()
        self.username_input = QLineEdit()
        self.login_frame = QFrame()
        self.backend = backend
        self.logger = Logger(__name__)
        self.username: str = ""
        self.password: str = ""
        self.toggle_password_action = None
        self.remember_me_checkbox = None

        self.init_ui()
        self.connect_signals()
        self.load_saved_credentials()

    def init_ui(self) -> None:
        """
        Initializes the UI components of the login page.
        """
        self.setWindowTitle("Login")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.login_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.login_frame.setFixedSize(500, 400)
        self.login_frame.setObjectName("loginFrame")

        form_layout = QVBoxLayout(self.login_frame)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(15)

        close_button = QPushButton("×")
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #888;
                font-size: 20px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                color: #333;
            }
            """
        )
        close_button.clicked.connect(self.navigate_to_site_details.emit)
        form_layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("src/UI/icons/Detectronic-logo.png")
        logo_label.setPixmap(
            logo_pixmap.scaled(
                100,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(logo_label)

        # Welcome text
        welcome_label = QLabel("Welcome back")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        form_layout.addWidget(welcome_label)

        self.username_input.setPlaceholderText("Username")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        for input_field in (self.username_input, self.password_input):
            input_field.setStyleSheet(
                """
                QLineEdit {
                    padding: 10px;
                    background-color: #F3F4F6;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    background-color: #E5E7EB;
                    outline: none;
                    border: 1px solid #3B82F6;
                }
                """
            )
            form_layout.addWidget(input_field)

        # Password visibility toggle
        self.toggle_password_action = QAction(self)
        self.toggle_password_action.setIcon(QIcon("src/UI/icons/eye-close.png"))
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility)
        self.password_input.addAction(
            self.toggle_password_action,
            QLineEdit.ActionPosition.TrailingPosition
        )

        # Remember Me checkbox
        self.remember_me_checkbox = QCheckBox("Remember Me")
        self.remember_me_checkbox.setStyleSheet(
            """
            QCheckBox { 
                font-size: 12px;
                color: #111827;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                background-color: white;
            }
            QCheckBox::indicator:unchecked {
                image: url(src/UI/icons/unchecked.png);
            }
            QCheckBox::indicator:checked {
                image: url(src/UI/icons/checkbox.png);
            }
            """
        )
        form_layout.addWidget(self.remember_me_checkbox)

        # Error message display
        self.error_label.setStyleSheet("color: red; font-size: 14px;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)

        # Login button
        login_button = QPushButton("Log In")
        login_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #3B82F6);
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #2563EB);
            }
            """
        )
        login_button.clicked.connect(self.login)
        form_layout.addWidget(login_button)

        layout.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )
        layout.addWidget(self.login_frame, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

    def connect_signals(self) -> None:
        """
        Connects signals to the backend slots.
        """
        self.backend.loginSuccessful.connect(self.on_login_success)
        self.backend.loginFailed.connect(self.on_login_failed)
        self.backend.busyChanged.connect(self.on_busy_changed)

    def toggle_password_visibility(self) -> None:
        """
        Toggles the visibility of the password field.
        """
        try:
            if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
                self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
                self.toggle_password_action.setIcon(QIcon("src/UI/icons/eye.png"))
            else:
                self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
                self.toggle_password_action.setIcon(QIcon("src/UI/icons/eye-close.png"))
        except Exception as e:
            self.logger.error(f"Error toggling password visibility: {e}")

    def clear_error(self) -> None:
        """
        Clears the error message.
        """
        self.error_label.setText("")
        self.error_label.setVisible(False)

    def login(self) -> None:
        """
        Handles the login action, including validation and saving login details.
        """
        try:
            self.username = self.username_input.text()
            self.password = self.password_input.text()
            remember_me = self.remember_me_checkbox.isChecked()
            validation_error = validate_credentials(self.username, self.password)

            if validation_error:
                self.error_label.setText(validation_error)
                self.error_label.setVisible(True)
                self.logger.error(f"Validation error: {validation_error}")
            else:
                self.backend.save_login_details(self.username, self.password, remember_me)
                self.login_successful.emit()
        except Exception as e:
            self.logger.error(f"Error in login action: {e}")
            self.error_label.setText("An error occurred. Please try again.")
            self.error_label.setVisible(True)

    def load_saved_credentials(self):
        """
        Load the credentials from the backend.
        """
        try:
            username, password, remember_me = self.backend.get_login_details()
            if remember_me:
                self.username_input.setText(username)
                self.password_input.setText(password)
                self.remember_me_checkbox.setChecked(True)
        except Exception as e:
            self.logger.error(f"Failed to load saved credentials: {e}")

    def on_busy_changed(self, is_busy: bool) -> None:
        """
        Handles changes to the busy state.
        """
        self.setEnabled(not is_busy)

    def on_login_success(self) -> None:
        """
        Handles successful login.
        """
        self.logger.info("Login successful")
        self.navigate_to_site_details.emit()

    def on_login_failed(self, message: str) -> None:
        """
        Handles failed login.
        """
        self.error_label.setText(message)
        self.error_label.setVisible(True)
