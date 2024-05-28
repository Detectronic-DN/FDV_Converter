from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QFormLayout,
)
from PySide6.QtCore import Qt


class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.username = ""
        self.password = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Username
        username_label = QLabel("Enter Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.textChanged.connect(self.clear_error)
        form_layout.addRow(username_label, self.username_input)

        # Password
        password_label = QLabel("Enter Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.clear_error)
        form_layout.addRow(password_label, self.password_input)

        # Show Password Checkbox
        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.stateChanged.connect(
            self.toggle_password_visibility
        )
        form_layout.addRow(self.show_password_checkbox)

        layout.addLayout(form_layout)

        # Error message display
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Buttons
        button_layout = QHBoxLayout()
        skip_button = QPushButton("Skip")
        next_button = QPushButton("Next")

        skip_button.clicked.connect(self.skip)
        next_button.clicked.connect(self.next)

        button_layout.addStretch()
        button_layout.addWidget(skip_button)
        button_layout.addWidget(next_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def clear_error(self):
        self.error_label.setText("")
        self.error_label.setVisible(False)

    def skip(self):
        print("Skipped")
        # Handle skip logic here

    def next(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        validation_error = self.validate_credentials(self.username, self.password)

        if validation_error:
            self.error_label.setText(validation_error)
            self.error_label.setVisible(True)
        else:
            print(f"Username: {self.username}, Password: {self.password}")
            # Store credentials or make API calls here

    def validate_credentials(self, username, password):
        if not username.strip() and not password.strip():
            return "Username and Password cannot be empty."
        elif not username.strip():
            return "Username cannot be empty."
        elif not password.strip():
            return "Password cannot be empty."
        else:
            return ""
