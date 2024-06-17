from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QDateTimeEdit,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
)
from PySide6.QtCore import QDateTime


class TimestampDialog(QDialog):
    def __init__(self, start_timestamp, end_timestamp, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Timestamps")

        layout = QVBoxLayout()

        # Start Timestamp
        start_label = QLabel("Start Timestamp:")
        self.start_edit = QDateTimeEdit(self)
        self.start_edit.setDateTime(
            QDateTime.fromString(start_timestamp, "yyyy-MM-dd HH:mm:ss")
        )
        self.start_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addWidget(start_label)
        layout.addWidget(self.start_edit)

        # End Timestamp
        end_label = QLabel("End Timestamp:")
        self.end_edit = QDateTimeEdit(self)
        self.end_edit.setDateTime(
            QDateTime.fromString(end_timestamp, "yyyy-MM-dd HH:mm:ss")
        )
        self.end_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addWidget(end_label)
        layout.addWidget(self.end_edit)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_timestamps)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        self.initial_start_timestamp = QDateTime.fromString(
            start_timestamp, "yyyy-MM-dd HH:mm:ss"
        )
        self.initial_end_timestamp = QDateTime.fromString(
            end_timestamp, "yyyy-MM-dd HH:mm:ss"
        )

    def validate_timestamps(self):
        new_start_timestamp = self.start_edit.dateTime()
        new_end_timestamp = self.end_edit.dateTime()

        if (
            new_start_timestamp < self.initial_start_timestamp
            or new_end_timestamp > self.initial_end_timestamp
        ):
            QMessageBox.warning(
                self,
                "Invalid Timestamps",
                "The selected timestamps are outside the valid range.",
            )
        elif new_start_timestamp > new_end_timestamp:
            QMessageBox.warning(
                self,
                "Invalid Timestamps",
                "The start timestamp cannot be later than the end timestamp.",
            )
        else:
            self.accept()

    def get_timestamps(self):
        start_timestamp = self.start_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_timestamp = self.end_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        return start_timestamp, end_timestamp
