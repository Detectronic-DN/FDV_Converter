from PySide6.QtCore import Qt, QRect
from PySide6.QtCore import Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtSvg import QSvgRenderer
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
    QTabBar,
    QStyleOptionTab,
    QStyledItemDelegate
)


class CustomTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setStyleSheet(
            """
            QTabBar::tab {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
            }
        """
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        option = QStyleOptionTab()

        for index in range(self.count()):
            self.initStyleOption(option, index)
            if self.currentIndex() == index:
                painter.fillRect(option.rect, QColor("white"))
                painter.setPen(QPen(QColor("#007bff"), 2))
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
            else:
                painter.fillRect(option.rect, QColor("#f0f0f0"))

            self.tabIcon(index).paint(painter, option.rect)
            painter.drawText(option.rect, Qt.AlignCenter, self.tabText(index))

        painter.end()


class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px 30px 5px 10px;
                min-width: 6em;
                color: #333333;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #e0e0e0;
                selection-background-color: #f0f0f0;
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                padding: 5px 10px;
                color: #333333;
                
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f0f0;
                color: #333333;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e0e0e0;
                color: #333333;
            }
        """)

        # Custom item delegate for hover effect
        delegate = QStyledItemDelegate(self)
        self.setItemDelegate(delegate)
        # SVG arrow
        self.arrow_svg = """<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 512 512"> <path 
        d="M233.4 406.6c12.5 12.5 32.8 12.5 45.3 0l192-192c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L256 338.7 
        86.6 169.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l192 192z"></path> </svg>"""
        self.svg_renderer = QSvgRenderer(self.arrow_svg.encode('utf-8'))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background
        if self.view().isVisible() or self.currentIndex() != -1:
            painter.fillRect(self.rect(), QColor('#f0f0f0'))
        else:
            painter.fillRect(self.rect(), QColor('white'))

        # Draw the border
        pen = QPen(QColor('#e0e0e0'))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 4, 4)

        # Draw the text
        painter.setPen(QColor('#333333'))
        text_rect = self.rect().adjusted(10, 0, -30, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.currentText())

        # Draw SVG arrow
        size = 16
        rect = QRect(self.width() - size - 10, (self.height() - size) // 2, size, size)
        self.svg_renderer.render(painter, rect)


class FDVPage(QWidget):
    back_button_clicked = Signal()

    def __init__(self, backend, filepath, site_id, start_timestamp, end_timestamp):
        super().__init__()
        self.back_button = None
        self.use_r3_button = None
        self.calculate_r3_button = None
        self.r3_value_field = None
        self.create_rainfall_button = None
        self.pipe_width_field = None
        self.pipe_height_field = None
        self.egg_type_combo_box = None
        self.rainfall_logs_display = None
        self.rainfall_column_combo_box = None
        self.rainfall_site_name_field = None
        self.fdv_logs_display = None
        self.create_fdv_button = None
        self.interim_reports_button = None
        self.pipe_size_field = None
        self.pipe_shape_combo_box = None
        self.velocity_column_combo_box = None
        self.depth_column_combo_box = None
        self.site_name_field = None
        self.tab_widget = None
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
        self.update_site_info(site_id, start_timestamp, end_timestamp)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBar(CustomTabBar())
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border-top: 1px solid #d0d0d0;
                background-color: white;
            }
        """
        )

        # FDV Converter Tab
        fdv_tab = QWidget()
        fdv_layout = QGridLayout()

        fdv_layout.addWidget(QLabel("Site Name:"), 0, 0)
        self.site_name_field = QLineEdit(self.site_id)
        self.site_name_field.setStyleSheet(
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
        fdv_layout.addWidget(self.site_name_field, 0, 1)

        fdv_layout.addWidget(QLabel("Depth Column:"), 1, 0)
        self.depth_column_combo_box = CustomComboBox()
        fdv_layout.addWidget(self.depth_column_combo_box, 1, 1)

        fdv_layout.addWidget(QLabel("Velocity Column:"), 2, 0)
        self.velocity_column_combo_box = CustomComboBox()
        fdv_layout.addWidget(self.velocity_column_combo_box, 2, 1)

        fdv_layout.addWidget(QLabel("Pipe Shape:"), 3, 0)
        self.pipe_shape_combo_box = CustomComboBox()
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
        self.pipe_size_field.setStyleSheet(
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
        fdv_layout.addWidget(self.pipe_size_field, 4, 1)

        self.interim_reports_button = QPushButton("Interim Reports")
        self.interim_reports_button.setStyleSheet("""
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
        """)
        fdv_layout.addWidget(self.interim_reports_button, 5, 0)

        self.create_fdv_button = QPushButton("Create FDV")
        self.create_fdv_button.setStyleSheet("""
            QPushButton {
                background-color: #40B3A2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 1.2px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: #368f81;
            }
        """)
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
        self.rainfall_site_name_field.setStyleSheet(
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
        self.rainfall_site_name_field.setReadOnly(True)
        rainfall_layout.addWidget(self.rainfall_site_name_field, 0, 1)

        rainfall_layout.addWidget(QLabel("Rainfall Column:"), 1, 0)
        self.rainfall_column_combo_box = CustomComboBox()
        rainfall_layout.addWidget(self.rainfall_column_combo_box, 1, 1)

        self.create_rainfall_button = QPushButton("Create Rainfall")
        self.create_rainfall_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                font-size: 16px;
                font-weight: 500;
                color: #FFFFFF;
                text-align: center;
                position: relative;
                cursor: pointer;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #2980b9,
                                            stop:1 #2c3e50);
            }
            QPushButton::before {
                content: "";
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: 100%;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(41, 128, 185, 0.5),
                                            stop:1 rgba(44, 62, 80, 0.5));
                z-index: -1;
            }
            QPushButton::after {
                content: "";
                position: absolute;
                left: 1px;
                top: 1px;
                right: 1px;
                bottom: 1px;
                border-radius: 7px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(52, 152, 219, 0.1),
                                            stop:1 rgba(44, 62, 80, 0.1));
                border: 1px solid rgba(41, 128, 185, 0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #3498db,
                                            stop:1 #34495e);
            }
        """)
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
        self.egg_type_combo_box = CustomComboBox()
        self.egg_type_combo_box.addItems(["Egg Type 1", "Egg Type 2"])
        r3_layout.addWidget(self.egg_type_combo_box, 0, 1)

        r3_layout.addWidget(QLabel("Pipe Width (mm):"), 1, 0)
        self.pipe_width_field = QLineEdit()
        self.pipe_width_field.setStyleSheet(
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
        r3_layout.addWidget(self.pipe_width_field, 1, 1)

        r3_layout.addWidget(QLabel("Pipe Height (mm):"), 2, 0)
        self.pipe_height_field = QLineEdit()
        self.pipe_height_field.setStyleSheet(
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
        r3_layout.addWidget(self.pipe_height_field, 2, 1)

        r3_layout.addWidget(QLabel("R3 Value (mm):"), 3, 0)
        self.r3_value_field = QLineEdit()
        self.r3_value_field.setStyleSheet(
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

        self.r3_value_field.setReadOnly(True)
        r3_layout.addWidget(self.r3_value_field, 3, 1)

        # In the init_ui method, update the styling for both buttons

        button_style = """
            QPushButton {
                border-radius: 18px;
                background-color: white;
                padding: 16px 40px;
                font-size: 16px;
                font-weight: 400;
                line-height: 1.5;
                letter-spacing: -0.32px;
                border: 2px solid black;
            }
        """

        self.calculate_r3_button = QPushButton("Calculate R3")
        self.calculate_r3_button.setStyleSheet(button_style)
        r3_layout.addWidget(self.calculate_r3_button, 4, 0)

        self.use_r3_button = QPushButton("Use R3 in FDV")
        self.use_r3_button.setStyleSheet(button_style)
        r3_layout.addWidget(self.use_r3_button, 4, 1)
        r3_calculator_tab.setLayout(r3_layout)
        self.tab_widget.addTab(r3_calculator_tab, "R3 Calculator")

        layout.addWidget(self.tab_widget)

        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet("""
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
                """)
        layout.addWidget(self.back_button)

    def update_site_info(self, site_id, start_timestamp, end_timestamp):
        self.site_id = site_id
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.site_name_field.setText(site_id)
        self.rainfall_site_name_field.setText(site_id)

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

    def on_depth_column_selected(self):
        self.selected_depth_column = self.depth_column_combo_box.currentText()

    def on_velocity_column_selected(self):
        self.selected_velocity_column = self.velocity_column_combo_box.currentText()

    def on_rainfall_column_selected(self):
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
