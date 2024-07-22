from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
    QFrame,
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
        self.show_password_checkbox = None
        self.password_input = QLineEdit()
        self.username_input = QLineEdit()
        self.login_frame = QFrame()
        self.backend = backend
        self.logger = Logger(__name__)
        self.username: str = ""
        self.password: str = ""

        self.init_ui()
        self.connect_signals()
        self.load_saved_credentials()

    def init_ui(self) -> None:
        """
        Initializes the UI components of the login page.
        """
        self.setWindowTitle("Login")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a spacer item for top and bottom
        top_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        bottom_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        # Add top spacer to the layout
        layout.addItem(top_spacer)

        # Create the frame for the login form without visible borders

        self.login_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.login_frame.setFixedSize(400, 350)
        self.login_frame.setObjectName("loginFrame")

        form_layout = QVBoxLayout(self.login_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # title
        title_label = QLabel("DD-EN Login")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        form_layout.addWidget(title_label)

        # Username
        username_label = QLabel("Enter Username:")
        username_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(
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
        self.username_input.textChanged.connect(self.clear_error)
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Enter Password:")
        password_label.setStyleSheet("font-size: 14px; font-weight: bold; ")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.username_input.styleSheet())
        self.password_input.textChanged.connect(self.clear_error)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)

        # Show Password Checkbox
        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.setStyleSheet(
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
                image: url(icons/unchecked.png);
            }
            QCheckBox::indicator:checked {
                image: url(icons/checkbox.png);
            }
                        
            """
        )
        self.show_password_checkbox.setEnabled(True)
        self.show_password_checkbox.stateChanged.connect(
            self.toggle_password_visibility
        )
        self.show_password_checkbox.raise_()
        form_layout.addWidget(self.show_password_checkbox)

        # Error message display
        self.error_label.setStyleSheet("color: red; font-size: 14px;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)

        # Buttons for further actions
        buttons_layout = QHBoxLayout()
        skip_button = QPushButton("Skip")
        next_button = QPushButton("Submit")
        next_button.setStyleSheet(
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
        skip_button.setStyleSheet(next_button.styleSheet())
        buttons_layout.addWidget(skip_button)
        buttons_layout.addWidget(next_button)

        form_layout.addLayout(buttons_layout)

        # Add the form layout to the login frame
        layout.addWidget(self.login_frame, 0, Qt.AlignmentFlag.AlignCenter)

        # Add bottom spacer to the layout
        layout.addItem(bottom_spacer)

        self.setLayout(layout)

        # Connections
        skip_button.clicked.connect(self.skip)
        next_button.clicked.connect(self.next)

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
            if self.show_password_checkbox.isChecked():
                self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        except Exception as e:
            self.logger.error(f"Error toggling password visibility: {e}")

    def clear_error(self) -> None:
        """
        Clears the error message.
        """
        self.error_label.setText("")
        self.error_label.setVisible(False)

    def skip(self) -> None:
        """
        Handles the skip action.
        """
        self.logger.info("Skipped")
        self.navigate_to_site_details.emit()

    def next(self) -> None:
        """
        Handles the next action, including validation and saving login details.
        """
        try:
            self.username = self.username_input.text()
            self.password = self.password_input.text()
            validation_error = validate_credentials(self.username, self.password)

            if validation_error:
                self.error_label.setText(validation_error)
                self.error_label.setVisible(True)
                self.logger.error(f"Validation error: {validation_error}")
            else:
                self.backend.save_login_details(self.username, self.password)
                self.login_successful.emit()
        except Exception as e:
            self.logger.error(f"Error in next action: {e}")
            self.error_label.setText("An error occurred. Please try again.")
            self.error_label.setVisible(True)

    def load_saved_credentials(self):
        """
        Load the credentials from the backend.
        """
        try:
            username, password = self.backend.get_login_details()
            if username:
                self.username_input.setText(username)
            if password:
                self.password_input.setText(password)
        except Exception as e:
            self.logger.error(f"Failed to Load the credentials: {e}")

    def on_busy_changed(self, is_busy: bool) -> None:
        """
        Handles changes to the busy state.
        """
        if is_busy:
            self.setEnabled(False)
        else:
            self.setEnabled(True)

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
