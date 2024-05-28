from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFormLayout,
    QTextEdit,
)


class SiteDetailsPage(QWidget):
    def __init__(self) -> None:
        """
        Initializes the SiteDetailsPage with UI components.
        """
        super().__init__()

        self.init_ui()

    def init_ui(self) -> None:
        """
        Initializes the UI components of the site details page.
        """
        layout = QVBoxLayout()

        # Form layout for site details
        form_layout = QFormLayout()

        # Site ID
        site_id_label = QLabel("Enter Site ID:")
        self.site_id_input = QLineEdit()
        self.site_id_input.setPlaceholderText("Site ID")
        form_layout.addRow(site_id_label, self.site_id_input)

        get_details_button = QPushButton("Get Site Details")
        form_layout.addRow(get_details_button)

        # Upload File
        upload_label = QLabel("Upload File:")
        self.upload_input = QLineEdit()
        self.upload_input.setPlaceholderText("Upload a CSV file")
        browse_button = QPushButton("Browse")

        upload_layout = QHBoxLayout()
        upload_layout.addWidget(self.upload_input)
        upload_layout.addWidget(browse_button)

        form_layout.addRow(upload_label, upload_layout)

        layout.addLayout(form_layout)

        # Site details display
        details_label = QLabel("Site Details")
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(details_label)
        layout.addWidget(self.details_text)

        # Buttons for further actions
        buttons_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        edit_timestamp_button = QPushButton("Edit Timestamp")
        continue_button = QPushButton("Continue")

        buttons_layout.addWidget(self.back_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(edit_timestamp_button)
        buttons_layout.addWidget(continue_button)

        layout.addLayout(buttons_layout)

        # Logs display
        logs_label = QLabel("Logs will be displayed here.")
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(logs_label)
        layout.addWidget(self.logs_text)

        self.setLayout(layout)
