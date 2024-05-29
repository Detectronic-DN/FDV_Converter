from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QGridLayout,
    QScrollArea,
    QTextEdit,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal


class FDVPage(QWidget):
    back_button_clicked = Signal()

    def __init__(self, backend, filepath, site_id, start_timestamp, end_timestamp):
        super().__init__()
        self.backend = backend
        self.filepath = filepath
        self.site_id = site_id
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp

        self.selected_depth_column = ""
        self.selected_velocity_column = ""
        self.selected_rainfall_column = ""

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Tab Widget
        self.tab_widget = QTabWidget()

        # FDV Converter Tab
        fdv_tab = QWidget()
        fdv_layout = QGridLayout()

        fdv_layout.addWidget(QLabel("Site Name:"), 0, 0)
        self.site_name_field = QLineEdit(self.site_id)
        fdv_layout.addWidget(self.site_name_field, 0, 1)

        fdv_layout.addWidget(QLabel("Depth Column:"), 1, 0)
        self.depth_column_combo_box = QComboBox()
        fdv_layout.addWidget(self.depth_column_combo_box, 1, 1)

        fdv_layout.addWidget(QLabel("Velocity Column:"), 2, 0)
        self.velocity_column_combo_box = QComboBox()
        fdv_layout.addWidget(self.velocity_column_combo_box, 2, 1)

        fdv_layout.addWidget(QLabel("Pipe Shape:"), 3, 0)
        self.pipe_shape_combo_box = QComboBox()
        self.pipe_shape_combo_box.addItems(
            [
                "Circular",
                "Rectangular",
                "Egg Type 1",
                "Egg Type 2",
                "Egg Type 2a",
                "Two Circles and a Rectangle",
            ]
        )
        fdv_layout.addWidget(self.pipe_shape_combo_box, 3, 1)

        fdv_layout.addWidget(QLabel("Pipe Size:"), 4, 0)
        self.pipe_size_field = QLineEdit()
        fdv_layout.addWidget(self.pipe_size_field, 4, 1)

        self.interim_reports_button = QPushButton("Interim Reports")
        fdv_layout.addWidget(self.interim_reports_button, 5, 0)

        self.create_fdv_button = QPushButton("Create FDV")
        fdv_layout.addWidget(self.create_fdv_button, 5, 1)

        fdv_layout.addWidget(QLabel("FDV Logs:"), 6, 0)
        self.fdv_logs_display = QTextEdit()
        self.fdv_logs_display.setReadOnly(True)
        self.fdv_logs_display.setPlaceholderText("No FDV file created yet")

        fdv_scroll_area = QScrollArea()
        fdv_scroll_area.setWidgetResizable(True)
        fdv_scroll_area.setWidget(self.fdv_logs_display)
        fdv_layout.addWidget(fdv_scroll_area, 7, 0, 1, 2)

        fdv_tab.setLayout(fdv_layout)
        self.tab_widget.addTab(fdv_tab, "FDV Converter")

        # Rainfall Tab
        rainfall_tab = QWidget()
        rainfall_layout = QGridLayout()

        rainfall_layout.addWidget(QLabel("Site Name:"), 0, 0)
        self.rainfall_site_name_field = QLineEdit(self.site_id)
        self.rainfall_site_name_field.setReadOnly(True)
        rainfall_layout.addWidget(self.rainfall_site_name_field, 0, 1)

        rainfall_layout.addWidget(QLabel("Rainfall Column:"), 1, 0)
        self.rainfall_column_combo_box = QComboBox()
        rainfall_layout.addWidget(self.rainfall_column_combo_box, 1, 1)

        self.create_rainfall_button = QPushButton("Create Rainfall")
        rainfall_layout.addWidget(self.create_rainfall_button, 2, 1)

        rainfall_layout.addWidget(QLabel("Rainfall Logs:"), 3, 0)

        self.rainfall_logs_display = QTextEdit()
        self.rainfall_logs_display.setReadOnly(True)
        self.rainfall_logs_display.setPlaceholderText("No Rainfall file created yet")
        rainfall_scroll_area = QScrollArea()
        rainfall_scroll_area.setWidgetResizable(True)
        rainfall_scroll_area.setWidget(self.rainfall_logs_display)
        rainfall_layout.addWidget(rainfall_scroll_area, 4, 0, 1, 2)

        rainfall_tab.setLayout(rainfall_layout)
        self.tab_widget.addTab(rainfall_tab, "Rainfall")

        # R3 Calculator Tab
        r3_calculator_tab = QWidget()
        r3_layout = QGridLayout()

        r3_layout.addWidget(QLabel("Egg Type:"), 0, 0)
        self.egg_type_combo_box = QComboBox()
        self.egg_type_combo_box.addItems(["Egg Type 1", "Egg Type 2"])
        r3_layout.addWidget(self.egg_type_combo_box, 0, 1)

        r3_layout.addWidget(QLabel("Pipe Width (mm):"), 1, 0)
        self.pipe_width_field = QLineEdit()
        r3_layout.addWidget(self.pipe_width_field, 1, 1)

        r3_layout.addWidget(QLabel("Pipe Height (mm):"), 2, 0)
        self.pipe_height_field = QLineEdit()
        r3_layout.addWidget(self.pipe_height_field, 2, 1)

        r3_layout.addWidget(QLabel("R3 Value (mm):"), 3, 0)
        self.r3_value_field = QLineEdit()
        self.r3_value_field.setReadOnly(True)
        r3_layout.addWidget(self.r3_value_field, 3, 1)

        self.calculate_r3_button = QPushButton("Calculate R3")
        r3_layout.addWidget(self.calculate_r3_button, 4, 0, 1, 2)

        self.use_r3_button = QPushButton("Use R3 in FDV")
        r3_layout.addWidget(self.use_r3_button, 5, 0, 1, 2)

        r3_calculator_tab.setLayout(r3_layout)
        self.tab_widget.addTab(r3_calculator_tab, "R3 Calculator")

        layout.addWidget(self.tab_widget)

        self.back_button = QPushButton("Back")
        layout.addWidget(self.back_button)

    def setup_connections(self):
        # Connect backend signals to the appropriate slots
        self.backend.columnsRetrieved.connect(self.on_columns_retrieved)
        self.backend.logMessage.connect(self.on_log_message)
        self.backend.fdvCreated.connect(self.on_fdv_created)
        self.backend.fdvError.connect(self.on_fdv_error)
        self.backend.interimReportCreated.connect(self.on_interim_report_created)
        self.backend.rainfallCreated.connect(self.on_rainfall_created)
        self.backend.rainfallError.connect(self.on_rainfall_error)
        self.backend.errorOccurred.connect(self.on_error_occurred)

        # Connect UI element signals to the appropriate slots
        self.depth_column_combo_box.currentIndexChanged.connect(
            self.on_depth_column_selected
        )
        self.velocity_column_combo_box.currentIndexChanged.connect(
            self.on_velocity_column_selected
        )
        self.rainfall_column_combo_box.currentIndexChanged.connect(
            self.on_rainfall_column_selected
        )

        self.interim_reports_button.clicked.connect(self.backend.create_interim_reports)
        self.create_fdv_button.clicked.connect(self.create_fdv)
        self.create_rainfall_button.clicked.connect(self.create_rainfall)
        self.calculate_r3_button.clicked.connect(self.calculate_r3)
        self.use_r3_button.clicked.connect(self.use_r3_in_fdv)
        self.back_button.clicked.connect(self.on_back_button_clicked)

    def on_columns_retrieved(self, columns):
        self.depth_column_combo_box.clear()
        self.velocity_column_combo_box.clear()
        self.rainfall_column_combo_box.clear()

        self.depth_column_combo_box.addItem("None")
        self.velocity_column_combo_box.addItem("None")

        for column in columns:
            self.depth_column_combo_box.addItem(column)
            self.velocity_column_combo_box.addItem(column)
            self.rainfall_column_combo_box.addItem(column)

        if self.selected_depth_column:
            index = self.depth_column_combo_box.findText(self.selected_depth_column)
            if index != -1:
                self.depth_column_combo_box.setCurrentIndex(index)

        if self.selected_velocity_column:
            index = self.velocity_column_combo_box.findText(
                self.selected_velocity_column
            )
            if index != -1:
                self.velocity_column_combo_box.setCurrentIndex(index)

        if self.selected_rainfall_column:
            index = self.rainfall_column_combo_box.findText(
                self.selected_rainfall_column
            )
            if index != -1:
                self.rainfall_column_combo_box.setCurrentIndex(index)

    def on_log_message(self, message):
        self.fdv_logs_display.append(message)

    def on_fdv_created(self, message):
        self.fdv_logs_display.append(message)

    def on_fdv_error(self, error_message):
        self.fdv_logs_display.append(error_message)

    def on_interim_report_created(self, message):
        self.fdv_logs_display.append(message)

    def on_rainfall_created(self, message):
        self.rainfall_logs_display.append(message)

    def on_rainfall_error(self, error_message):
        self.rainfall_logs_display.append(error_message)

    def on_error_occurred(self, error_message):
        self.fdv_logs_display.append(error_message)

    def on_depth_column_selected(self, index):
        self.selected_depth_column = self.depth_column_combo_box.currentText()

    def on_velocity_column_selected(self, index):
        self.selected_velocity_column = self.velocity_column_combo_box.currentText()

    def on_rainfall_column_selected(self, index):
        self.selected_rainfall_column = self.rainfall_column_combo_box.currentText()

    def create_fdv(self):
        depth_column = (
            "" if self.selected_depth_column == "None" else self.selected_depth_column
        )
        velocity_column = (
            ""
            if self.selected_velocity_column == "None"
            else self.selected_velocity_column
        )

        if self.pipe_size_field.text() is None or self.pipe_size_field.text() == "":
            pipe_size_param = 0

        else:
            pipe_size_param = self.pipe_size_field.text()

        self.backend.create_fdv(
            self.site_name_field.text(),
            self.pipe_shape_combo_box.currentText(),
            pipe_size_param,
            depth_column,
            velocity_column,
        )

    def create_rainfall(self):
        self.backend.create_rainfall(self.site_id, self.selected_rainfall_column)

    def calculate_r3(self):
        width = float(self.pipe_width_field.text())
        height = float(self.pipe_height_field.text())
        egg_type = self.egg_type_combo_box.currentText()
        r3_value = self.backend.calculate_r3(width, height, egg_type)
        self.r3_value_field.setText(f"{r3_value:.2f}")

    def use_r3_in_fdv(self):
        pipe_size = f"{self.pipe_width_field.text()},{self.pipe_height_field.text()},{self.r3_value_field.text()}"
        self.pipe_size_field.setText(pipe_size)
        self.tab_widget.setCurrentIndex(0)

    def on_back_button_clicked(self):
        self.back_button_clicked.emit()
        self.fdv_logs_display.clear()
        self.rainfall_logs_display.clear()
