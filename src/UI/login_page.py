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
from PySide6.QtCore import Qt, Signal
from src.backend.backend import Backend
from src.logger.logger import Logger


class LoginPage(QWidget):
    navigate_to_site_details = Signal()

    def __init__(self) -> None:
        """
        Initializes the LoginPage with UI components and backend integration.
        """
        super().__init__()

        self.backend = Backend()
        self.logger = Logger(__name__)
        self.username: str = ""
        self.password: str = ""

        self.init_ui()

    def init_ui(self) -> None:
        """
        Initializes the UI components of the login page.
        """
        layout = QVBoxLayout()

        # Create a spacer item for top and bottom
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add top spacer to the layout
        layout.addItem(top_spacer)

        # Create the frame for the login form without visible borders
        self.login_frame = QFrame()
        self.login_frame.setFrameShape(QFrame.NoFrame)
        self.login_frame.setFixedSize(400, 200) 

        form_layout = QVBoxLayout(self.login_frame)

        # Username
        username_label = QLabel("Enter Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.textChanged.connect(self.clear_error)
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Enter Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.clear_error)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)

        # Show Password Checkbox
        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.stateChanged.connect(
            self.toggle_password_visibility
        )
        form_layout.addWidget(self.show_password_checkbox)

        # Error message display
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)

        # Buttons for further actions
        buttons_layout = QHBoxLayout()
        skip_button = QPushButton("Skip")
        next_button = QPushButton("Next")

        buttons_layout.addWidget(skip_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(next_button)

        form_layout.addLayout(buttons_layout)

        # Add the form layout to the login frame
        layout.addWidget(self.login_frame, 0, Qt.AlignCenter)

        # Add bottom spacer to the layout
        layout.addItem(bottom_spacer)

        self.setLayout(layout)

        # Connections
        skip_button.clicked.connect(self.skip)
        next_button.clicked.connect(self.next)

    def toggle_password_visibility(self) -> None:
        """
        Toggles the visibility of the password field.
        """
        try:
            if self.show_password_checkbox.isChecked():
                self.password_input.setEchoMode(QLineEdit.Normal)
            else:
                self.password_input.setEchoMode(QLineEdit.Password)
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
            validation_error = self.validate_credentials(self.username, self.password)

            if validation_error:
                self.error_label.setText(validation_error)
                self.error_label.setVisible(True)
                self.logger.error(f"Validation error: {validation_error}")
            else:
                self.backend.save_login_details(self.username, self.password)
                self.logger.info(
                    f"Username: {self.username}, Password: {self.password}"
                )
                self.navigate_to_site_details.emit()
        except Exception as e:
            self.logger.error(f"Error in next action: {e}")
            self.error_label.setText("An error occurred. Please try again.")
            self.error_label.setVisible(True)

    def validate_credentials(self, username: str, password: str) -> str:
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
