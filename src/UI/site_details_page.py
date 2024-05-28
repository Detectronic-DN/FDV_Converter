# src/UI/site_details_page.py

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QGroupBox,
    QTextEdit,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from src.logger.logger import Logger
from src.UI.worker_class import Worker


class SiteDetailsPage(QWidget):
    back_button_clicked = Signal()

    def __init__(self, backend) -> None:
        """
        Initializes the SiteDetailsPage with UI components.
        """
        super().__init__()

        self.backend = backend
        self.logger = Logger(__name__, emit_func=self.append_log)

        # Worker thread setup
        self.worker = Worker(backend)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.worker.logMessage.connect(self.on_log_message)
        self.worker.siteDetailsRetrieved.connect(self.on_site_details_retrieved)
        self.worker.errorOccurred.connect(self.on_error_occurred)
        self.worker.busyChanged.connect(self.on_busy_changed)

        self.siteId = ""
        self.siteName = ""
        self.startTimestamp = ""
        self.endTimestamp = ""
        self.filePath = ""
        self.isBusy = False
        self.folderpath = ""

        self.init_ui()

    def init_ui(self) -> None:
        """
        Initializes the UI components of the site details page.
        """
        layout = QVBoxLayout()

        # Site ID Input Section
        site_id_layout = QHBoxLayout()
        site_id_label = QLabel("Enter Site ID:")
        self.site_id_input = QLineEdit()
        self.site_id_input.setPlaceholderText("Site ID")
        self.site_id_input.returnPressed.connect(self.get_site_details)
        site_id_layout.addWidget(site_id_label)
        site_id_layout.addWidget(self.site_id_input)
        layout.addLayout(site_id_layout)

        get_details_button = QPushButton("Get Site Details")
        get_details_button.clicked.connect(self.get_site_details)
        layout.addWidget(get_details_button, alignment=Qt.AlignRight)

        # File Upload Section
        file_upload_layout = QHBoxLayout()
        upload_label = QLabel("Upload File:")
        self.upload_input = QLineEdit()
        self.upload_input.setPlaceholderText("Upload a CSV file")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.open_file_dialog)
        file_upload_layout.addWidget(upload_label)
        file_upload_layout.addWidget(self.upload_input)
        file_upload_layout.addWidget(browse_button)
        layout.addLayout(file_upload_layout)

        # Site Details Display Section
        site_details_groupbox = QGroupBox("Site Details")
        site_details_layout = QVBoxLayout()

        self.site_id_label = QLabel("Site ID: ")
        self.site_name_label = QLabel("Site Name: ")
        self.start_timestamp_label = QLabel("Start Timestamp: ")
        self.end_timestamp_label = QLabel("End Timestamp: ")

        site_details_layout.addWidget(self.site_id_label)
        site_details_layout.addWidget(self.site_name_label)
        site_details_layout.addWidget(self.start_timestamp_label)
        site_details_layout.addWidget(self.end_timestamp_label)

        site_details_groupbox.setLayout(site_details_layout)
        layout.addWidget(site_details_groupbox)

        # Action Buttons
        action_buttons_layout = QHBoxLayout()
        edit_timestamp_button = QPushButton("Edit Timestamp")
        edit_timestamp_button.clicked.connect(self.edit_timestamps)
        continue_button = QPushButton("Continue")
        continue_button.clicked.connect(self.continue_to_next)

        action_buttons_layout.addWidget(edit_timestamp_button)
        action_buttons_layout.addWidget(continue_button)
        layout.addLayout(action_buttons_layout)

        # Back Button
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back_button_clicked.emit)
        back_button_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        layout.addLayout(back_button_layout)

        # Logs Display Section
        logs_layout = QVBoxLayout()
        logs_label = QLabel("Logs")
        self.logs_display = QTextEdit()
        self.logs_display.setPlaceholderText("No logs available")
        self.logs_display.setReadOnly(True)
        logs_layout.addWidget(logs_label)
        logs_layout.addWidget(self.logs_display)
        layout.addLayout(logs_layout)

        self.setLayout(layout)

    def open_file_dialog(self) -> None:
        """
        Opens a file dialog to select a CSV file.
        """
        file_dialog = QFileDialog(self, "Select a CSV File", "", "CSV Files (*.csv)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.upload_input.setText(file_path)
            self.backend.upload_csv_file(file_path)

    def open_folder_dialog(self) -> None:
        """
        Opens a folder dialog to select a folder.
        """
        folder_dialog = QFileDialog(self, "Select a Folder", "", "")
        folder_dialog.setFileMode(QFileDialog.Directory)
        if folder_dialog.exec():
            folder_path = folder_dialog.selectedFiles()[0]
            self.folderpath = folder_path

    def get_site_details(self) -> None:
        """
        Retrieves site details using the provided site ID.
        """
        site_id = self.site_id_input.text().strip()
        if site_id:
            self.open_folder_dialog()
            if self.folderpath:
                # Run the CSV download in a separate thread
                self.worker.download_csv_file.emit(site_id, self.folderpath)
            else:
                self.logger.warning("Folder selection cancelled.")
        else:
            self.logger.warning("Please enter a Site ID.")

    def edit_timestamps(self) -> None:
        """
        Edits the timestamps using the backend.
        """
        self.backend.edit_timestamps(self.startTimestamp, self.endTimestamp)

    def continue_to_next(self) -> None:
        """
        Continues to the next page with the current site details.
        """
        # Implement navigation logic here
        pass

    @Slot(str, str, str, str)
    def on_site_details_retrieved(
        self, site_id, site_name, start_timestamp, end_timestamp
    ) -> None:
        """
        Handles the signal when site details are retrieved.
        """
        self.site_id_label.setText(f"Site ID: {site_id}")
        self.site_name_label.setText(f"Site Name: {site_name}")
        self.start_timestamp_label.setText(f"Start Timestamp: {start_timestamp}")
        self.end_timestamp_label.setText(f"End Timestamp: {end_timestamp}")
        self.siteId = site_id
        self.siteName = site_name
        self.startTimestamp = start_timestamp
        self.endTimestamp = end_timestamp

    @Slot(str)
    def on_error_occurred(self, error_message) -> None:
        """
        Handles the signal when an error occurs.
        """
        self.logs_display.append(error_message)

    @Slot(str)
    def on_log_message(self, msg) -> None:
        """
        Handles the signal for log messages.
        """
        self.logs_display.append(msg)

    @Slot(bool)
    def on_busy_changed(self, is_busy) -> None:
        """
        Handles the signal when the busy state changes.
        """
        self.isBusy = is_busy
        if is_busy:
            self.logs_display.append("Processing, please wait...")
        else:
            self.logs_display.append("Processing complete.")
        # Implement UI changes for busy state if necessary

    def append_log(self, log_message: str):
        """
        Appends a log message to the logs display.
        """
        self.logs_display.append(log_message)
