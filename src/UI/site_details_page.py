from PySide6.QtCore import Qt, QPoint
from PySide6.QtCore import Signal, Slot, QThread
from PySide6.QtGui import QPainter, QColor, QPen
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
    QStackedWidget,
    QGridLayout,
    QFrame,
)

from src.logger.logger import Logger
from src.worker.api_worker import Worker
from src.worker.file_worker import UploadWorker


class SiteDetailsPage(QWidget):
    back_button_clicked = Signal()
    continue_to_next = Signal()

    def __init__(self, backend, stack: QStackedWidget) -> None:
        """
        Initializes the SiteDetailsPage with UI components.
        """
        super().__init__()

        self.logs_display = None
        self.back_button = None
        self.end_timestamp_label = None
        self.site_name_label = None
        self.start_timestamp_label = None
        self.site_id_label = None
        self.upload_input = None
        self.site_id_input = None
        self.backend = backend
        self.stack = stack
        self.logger = Logger(__name__, emit_func=self.append_log)

        # Worker thread setup for downloading
        self.worker = Worker(backend)
        self.worker_thread = QThread()
        self.worker_thread.quit()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.worker.logMessage.connect(self.on_log_message)
        self.worker.siteDetailsRetrieved.connect(self.on_site_details_retrieved)
        self.worker.errorOccurred.connect(self.on_error_occurred)
        self.worker.busyChanged.connect(self.on_busy_changed)

        # Worker thread setup for uploading
        self.upload_worker = UploadWorker(backend)
        self.upload_worker_thread = QThread()
        self.upload_worker_thread.quit()

        self.upload_worker.moveToThread(self.upload_worker_thread)
        self.upload_worker_thread.start()

        self.upload_worker.logMessage.connect(self.on_log_message)
        self.upload_worker.siteDetailsRetrieved.connect(self.on_site_details_retrieved)
        self.upload_worker.errorOccurred.connect(self.on_error_occurred)
        self.upload_worker.busyChanged.connect(self.on_busy_changed)

        self.siteId = ""
        self.siteName = ""
        self.startTimestamp = ""
        self.endTimestamp = ""
        self.filePath = ""
        self.isBusy = False
        self.folder_path = ""

        self.init_ui()

    def init_ui(self) -> None:
        """
        Initializes the UI components of the site details page.
        """
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Site ID Input Section
        site_id_layout = QHBoxLayout()
        site_id_label = QLabel("Site ID:")
        site_id_label.setStyleSheet("font-size: 14px;")
        self.site_id_input = QLineEdit()
        self.site_id_input.setPlaceholderText("Enter Site ID")
        self.site_id_input.setStyleSheet(
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
        self.site_id_input.returnPressed.connect(self.get_site_details)
        get_details_button = QPushButton("Get Site Details")
        get_details_button.setFixedSize(150, 40)
        get_details_button.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #bbbbbb;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb(128, 128, 255), stop:1 rgb(183, 128, 255));
            }
            QPushButton:hover {
                background-color: #B780FF;
            }   
        """
        )
        get_details_button.clicked.connect(self.get_site_details)
        site_id_layout.addWidget(site_id_label)
        site_id_layout.addWidget(self.site_id_input)
        site_id_layout.addWidget(get_details_button)
        layout.addLayout(site_id_layout)

        # File Upload Section
        file_upload_layout = QHBoxLayout()
        upload_label = QLabel("Upload File:")
        self.upload_input = QLineEdit()
        self.upload_input.setPlaceholderText("Upload a CSV or Excel file")
        self.upload_input.setStyleSheet(self.site_id_input.styleSheet())
        browse_button = QPushButton("Add File")
        browse_button.setFixedSize(100, 40)
        browse_button.setStyleSheet(
            """
            QPushButton {
                background-color: #307750;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #469b61;
            }
        """
        )
        browse_button.clicked.connect(self.open_file_dialog)
        file_upload_layout.addWidget(upload_label)
        file_upload_layout.addWidget(self.upload_input)
        file_upload_layout.addWidget(browse_button)
        layout.addLayout(file_upload_layout)

        # Site Details Display Section
        site_details_groupbox = QGroupBox()
        site_details_groupbox.setTitle("Site Details")
        site_details_groupbox.setStyleSheet(
            """
        QGroupBox {
            border: 1px solid gray;
            border-color: #FF17365D;
            margin-top: 27px;
            font-size: 14px;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            padding: 5px;
            background-color: #FF17365D;
            color: rgb(255, 255, 255);
        }

        """
        )
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
        action_buttons_layout = QGridLayout()
        action_buttons_layout.setSpacing(10)  # Space between buttons

        button_style = """
                    QPushButton {
                        background-color: #5a67d8;
                        color: #fff;
                        border: none;
                        border-radius: 8px;
                        padding: 15px 20px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #4c51bf;
                    }
                """

        edit_timestamp_button = QPushButton("Edit Timestamp")
        edit_timestamp_button.setStyleSheet(button_style)
        edit_timestamp_button.clicked.connect(self.edit_timestamps)

        continue_button = QPushButton("Continue")
        continue_button.setStyleSheet(
            button_style.replace("#5a67d8", "#404660").replace("#4c51bf", "#3A4059")
        )
        continue_button.setCursor(Qt.PointingHandCursor)

        # Custom paint event for continue button (arrow)
        def paintEvent(event):
            QPushButton.paintEvent(continue_button, event)
            painter = QPainter(continue_button)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(
                QPen(QColor("#fff"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            )
            arrow_size = 10
            x = continue_button.width() - 25  # Adjust arrow position
            y = continue_button.height() // 2
            painter.drawLine(QPoint(x, y), QPoint(x + arrow_size, y))
            painter.drawLine(
                QPoint(x + arrow_size, y), QPoint(x + arrow_size - 5, y - 5)
            )
            painter.drawLine(
                QPoint(x + arrow_size, y), QPoint(x + arrow_size - 5, y + 5)
            )

        continue_button.paintEvent = paintEvent
        continue_button.clicked.connect(self.continue_to_next_page)

        # Add buttons to the grid layout
        action_buttons_layout.addWidget(edit_timestamp_button, 0, 0)
        action_buttons_layout.addWidget(continue_button, 0, 1)

        # Set column stretch to make buttons expand horizontally
        action_buttons_layout.setColumnStretch(0, 1)
        action_buttons_layout.setColumnStretch(1, 1)

        # Set a fixed height for both buttons
        edit_timestamp_button.setFixedHeight(50)
        continue_button.setFixedHeight(50)

        layout.addLayout(action_buttons_layout)

        layout.addLayout(action_buttons_layout)

        # Back Button
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet(
            """
            QPushButton {
                background-color: #a0aec0;
                color: #1a202c;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #718096;
            }
        """
        )
        self.back_button.clicked.connect(self.on_back_button_clicked)
        back_button_layout.addWidget(
            self.back_button, alignment=Qt.AlignmentFlag.AlignLeft
        )
        layout.addLayout(back_button_layout)

        # Logs Display Section
        logs_frame = QFrame()
        logs_frame.setObjectName("logsFrame")
        logs_frame.setStyleSheet(
            """
            #logsFrame {
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
        """
        )
        logs_layout = QVBoxLayout(logs_frame)
        logs_label = QLabel("Logs")
        logs_label.setStyleSheet(
            """
            font-size: 14px;
            color: #374151;
            margin-bottom: 5px;
        """
        )
        self.logs_display = QTextEdit()

        self.logs_display.setPlaceholderText("No logs available")
        self.logs_display.setReadOnly(True)
        self.logs_display.setStyleSheet(
            """
                    QTextEdit {
                        border: 1px solid #e5e7eb;
                        border-radius: 4px;
                        background-color: white;
                        padding: 8px;
                        font-family: monospace;
                        font-size: 12px;
                    }
                """
        )
        logs_layout.addWidget(logs_label)
        logs_layout.addWidget(self.logs_display)
        layout.addWidget(logs_frame)
        layout.addLayout(logs_layout)
        self.setLayout(layout)

    def open_file_dialog(self) -> None:
        """
        Opens a file dialog to select a CSV or Excel file.
        """
        file_dialog = QFileDialog(
            self, "Select a CSV or Excel File", "", "Files (*.csv *.xls *.xlsx)"
        )
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.upload_input.setText(file_path)
            self.clear_site_details()
            # Run the CSV or Excel upload in a separate thread
            self.upload_worker.upload_csv_file.emit(file_path)

    def open_folder_dialog(self) -> None:
        """
        Opens a folder dialog to select a folder.
        """
        folder_dialog = QFileDialog(self, "Select a Folder", "", "")
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        if folder_dialog.exec():
            folder_path = folder_dialog.selectedFiles()[0]
            self.folder_path = folder_path

    def get_site_details(self) -> None:
        """
        Retrieves site details using the provided site ID.
        """
        site_id = self.site_id_input.text().strip()
        if site_id:
            self.open_folder_dialog()
            if self.folder_path:
                self.clear_site_details()
                # Run the CSV download in a separate thread
                self.worker.download_csv_file.emit(site_id, self.folder_path)
            else:
                self.logger.warning("Folder selection cancelled.")
        else:
            self.logger.warning("Please enter a Site ID.")

    def edit_timestamps(self) -> None:
        """
        Edits the timestamps using the backend.
        """
        self.backend.edit_timestamps(self.startTimestamp, self.endTimestamp)

    def continue_to_next_page(self) -> None:
        """
        Emits signal to continue to the next page.
        """
        self.continue_to_next.emit()
        self.backend.retrieve_columns()

    @Slot()
    def on_back_button_clicked(self):
        """Handles the back button click event."""
        self.back_button_clicked.emit()
        self.close_threads()
        self.logs_display.clear()

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

    def append_log(self, log_message: str):
        """
        Appends a log message to the logs display.
        """
        self.logs_display.append(log_message)

    def close_threads(self):
        """Closes the worker threads gracefully."""
        self.worker_thread.quit()
        self.worker_thread.wait()

        self.upload_worker_thread.quit()
        self.upload_worker_thread.wait()

    def clear_logs(self) -> None:
        """
        Clears the logs display widget.
        """
        self.logs_display.clear()

    def clear_site_details(self):
        self.site_id_label.setText("Site ID: ")
        self.site_name_label.setText("Site Name: ")
        self.start_timestamp_label.setText("Start Timestamp: ")
        self.end_timestamp_label.setText("End Timestamp: ")
        self.siteId = ""
        self.siteName = ""
        self.startTimestamp = ""
        self.endTimestamp = ""
        self.filePath = ""
