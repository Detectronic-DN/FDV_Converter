from PySide6.QtCore import Qt, QRect, Signal, Slot, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QMovie, QPaintEvent
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
    QStyledItemDelegate,
    QFrame,
)
from src.logger.logger import Logger


class CustomTabBar(QTabBar):
    def __init__(self, parent: QWidget = None) -> None:
        """
        Initializes a new instance of the CustomTabBar class.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.

        Returns:
            None
        """
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

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Override the paintEvent method to customize the appearance of the tab bar.

        Args:
            event (QPaintEvent): The paint event.

        Returns:
            None
        """
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
    def __init__(self, parent=None) -> None:
        """
        CustomComboBox class for styled combobox with SVG arrow.

        Args:
            parent: The parent widget (default None).
        """
        super().__init__(parent)
        self.setStyleSheet(
            """
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
            """
        )

        delegate = QStyledItemDelegate(self)
        self.setItemDelegate(delegate)
        self.arrow_svg = """<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 512 512"> <path 
        d="M233.4 406.6c12.5 12.5 32.8 12.5 45.3 0l192-192c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L256 338.7 
        86.6 169.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l192 192z"></path> </svg>"""
        self.svg_renderer = QSvgRenderer(self.arrow_svg.encode("utf-8"))

    def paintEvent(self, event) -> None:
        """
        Paint event to draw the styled combobox.

        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.view().isVisible() or self.currentIndex() != -1:
            painter.fillRect(self.rect(), QColor("#f0f0f0"))
        else:
            painter.fillRect(self.rect(), QColor("white"))

        pen = QPen(QColor("#e0e0e0"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 4, 4)

        painter.setPen(QColor("#333333"))
        text_rect = self.rect().adjusted(10, 0, -30, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.currentText())

        size = 16
        rect = QRect(self.width() - size - 10, (self.height() - size) // 2, size, size)
        self.svg_renderer.render(painter, rect)


class FDVPage(QWidget):
    back_button_clicked = Signal()

    def __init__(self, backend, filepath, site_id, start_timestamp, end_timestamp):
        """
        Initializes the FDVPage with the given backend, filepath, site ID, start timestamp, and end timestamp.

        Args:
            backend: The backend object.
            filepath: The file path.
            site_id: The site ID.
            start_timestamp: The start timestamp.
            end_timestamp: The end timestamp.
        """
        super().__init__()
        self.backend = backend
        self.filepath = filepath
        self.site_id = site_id
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.spinner = None
        self.logger = Logger(__name__)

        self.selected_depth_column = ""
        self.selected_velocity_column = ""
        self.selected_rainfall_column = ""

        self.init_ui()
        self.setup_connections()
        self.update_site_info(site_id, start_timestamp, end_timestamp)

    def setup_spinners(self):
        """
        setups the spinner animation
        """
        self.spinner = QLabel(self)
        movie = QMovie("icons/spinner.gif")
        self.spinner.setMovie(movie)
        movie.start()
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setFixedSize(50, 50)
        self.spinner.hide()

    def init_ui(self):
        """
        Initializes the user interface with a tab widget containing three tabs: "FDV Converter", "Rainfall", and "R3 Calculator".

        The "FDV Converter" tab contains various input fields and buttons for converting FDV data. It includes fields for site name, depth column, velocity column, pipe shape, pipe size, and buttons for creating interim reports and generating the FDV file. The logs display section shows the FDV logs.

        The "Rainfall" tab contains input fields and buttons for generating rainfall data. It includes fields for site name, rainfall column, and buttons for creating rainfall and generating rainfall totals. The logs display section shows the rainfall logs.

        The "R3 Calculator" tab contains input fields and buttons for calculating the R3 value. It includes fields for egg type, pipe width, pipe height, and buttons for calculating R3 and using R3 in the FDV file.

        The styling for both buttons is updated in the init_ui method.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        layout = QVBoxLayout(self)

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
        self.pipe_size_field.setStyleSheet(self.site_name_field.styleSheet())
        fdv_layout.addWidget(self.pipe_size_field, 4, 1)

        self.interim_reports_button = QPushButton("Interim Reports")
        self.interim_reports_button.setStyleSheet(
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
        self.interim_reports_button.clicked.connect(self.backend.create_interim_reports)
        fdv_layout.addWidget(self.interim_reports_button, 5, 0)

        self.create_fdv_button = QPushButton("Create FDV")
        self.create_fdv_button.setStyleSheet(
            """
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
            """
        )
        self.create_fdv_button.clicked.connect(self.create_fdv)
        fdv_layout.addWidget(self.create_fdv_button, 5, 1)

        self.setup_spinners()
        fdv_layout.addWidget(self.spinner, 6, 0, 1, 2, alignment=Qt.AlignCenter)

        fdv_tab.setLayout(fdv_layout)
        self.tab_widget.addTab(fdv_tab, "FDV Converter")

        # Rainfall Tab
        rainfall_tab = QWidget()
        rainfall_layout = QGridLayout()

        rainfall_layout.addWidget(QLabel("Site Name:"), 0, 0)
        self.rainfall_site_name_field = QLineEdit(self.site_id)
        self.rainfall_site_name_field.setStyleSheet(self.site_name_field.styleSheet())
        self.rainfall_site_name_field.setReadOnly(True)
        rainfall_layout.addWidget(self.rainfall_site_name_field, 0, 1)

        rainfall_layout.addWidget(QLabel("Rainfall Column:"), 1, 0)
        self.rainfall_column_combo_box = CustomComboBox()
        rainfall_layout.addWidget(self.rainfall_column_combo_box, 1, 1)

        self.create_rainfall_button = QPushButton("Create Rainfall")
        self.create_rainfall_button.setStyleSheet(self.create_fdv_button.styleSheet())
        self.create_rainfall_button.clicked.connect(self.create_rainfall)
        rainfall_layout.addWidget(self.create_rainfall_button, 2, 1)

        self.rainfall_totals_button = QPushButton("Generate Rainfall Totals")
        self.rainfall_totals_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.rainfall_totals_button.clicked.connect(self.generate_rainfall_totals)
        rainfall_layout.addWidget(self.rainfall_totals_button, 2, 0)

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
        self.pipe_width_field.setStyleSheet(self.site_name_field.styleSheet())
        r3_layout.addWidget(self.pipe_width_field, 1, 1)

        r3_layout.addWidget(QLabel("Pipe Height (mm):"), 2, 0)
        self.pipe_height_field = QLineEdit()
        self.pipe_height_field.setStyleSheet(self.site_name_field.styleSheet())
        r3_layout.addWidget(self.pipe_height_field, 2, 1)

        r3_layout.addWidget(QLabel("R3 Value (mm):"), 3, 0)
        self.r3_value_field = QLineEdit()
        self.r3_value_field.setStyleSheet(self.site_name_field.styleSheet())
        self.r3_value_field.setReadOnly(True)
        r3_layout.addWidget(self.r3_value_field, 3, 1)

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
        self.calculate_r3_button.clicked.connect(self.calculate_r3)
        r3_layout.addWidget(self.calculate_r3_button, 4, 0)

        self.use_r3_button = QPushButton("Use R3 in FDV")
        self.use_r3_button.setStyleSheet(button_style)
        self.use_r3_button.clicked.connect(self.use_r3_in_fdv)
        r3_layout.addWidget(self.use_r3_button, 4, 1)

        r3_calculator_tab.setLayout(r3_layout)
        self.tab_widget.addTab(r3_calculator_tab, "R3 Calculator")

        layout.addWidget(self.tab_widget)

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
        layout.addWidget(self.back_button)

    def update_site_info(self, site_id, start_timestamp, end_timestamp):
        self.site_id = site_id
        """
        Updates the site information with the provided site ID, start timestamp, and end timestamp.
        
        Args:
            site_id: The ID of the site.
            start_timestamp: The start timestamp.
            end_timestamp: The end timestamp.
        """
        self.site_id = site_id
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.site_name_field.setText(site_id)
        self.rainfall_site_name_field.setText(site_id)

    def setup_connections(self):
        """
        Connects the backend signals to the appropriate slots.

        This function sets up the connections between the backend signals and the corresponding slots in the FDVPage.
        It connects the `columnsRetrieved` signal from the backend to the `on_columns_retrieved` slot, the `busyChanged` signal to the `on_busy_changed` slot, and the `currentIndexChanged` signals from the `depth_column_combo_box`, `velocity_column_combo_box`, and `rainfall_column_combo_box` to their respective slots.

        Parameters:
            None

        Returns:
            None
        """
        self.backend.columnsRetrieved.connect(self.on_columns_retrieved)
        self.backend.busyChanged.connect(self.on_busy_changed)
        self.depth_column_combo_box.currentIndexChanged.connect(
            self.on_depth_column_selected
        )
        self.velocity_column_combo_box.currentIndexChanged.connect(
            self.on_velocity_column_selected
        )
        self.rainfall_column_combo_box.currentIndexChanged.connect(
            self.on_rainfall_column_selected
        )

    def on_columns_retrieved(self, columns):
        """
        Updates the columns in the UI based on the retrieved column names.

        Args:
            columns: A list of column names to be displayed in the combo boxes.

        Returns:
            None
        """
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

    def on_depth_column_selected(self):
        """
        Assigns the current text of the depth column combo box to the selected_depth_column attribute.
        """
        self.selected_depth_column = self.depth_column_combo_box.currentText()

    def on_velocity_column_selected(self):
        """
        Sets the `selected_velocity_column` attribute to the current text of the `velocity_column_combo_box`.

        This function is called when the user selects a new item in the `velocity_column_combo_box`. It retrieves the current text of the combo box and assigns it to the `selected_velocity_column` attribute.

        Parameters:
            None

        Returns:
            None
        """
        self.selected_velocity_column = self.velocity_column_combo_box.currentText()

    def on_rainfall_column_selected(self):
        """
        Sets the selected rainfall column based on the current text of the rainfall column combo box.

        This function retrieves the current text of the `rainfall_column_combo_box` and assigns it to the `selected_rainfall_column` attribute.

        Parameters:
            None

        Returns:
            None
        """
        self.selected_rainfall_column = self.rainfall_column_combo_box.currentText()

    @Slot(bool)
    def on_busy_changed(self, is_busy):
        """
        A function that handles the change in the busy state.

        Parameters:
            is_busy (bool): A boolean indicating whether the application is in a busy state.

        Returns:
            None
        """
        if is_busy:
            self.logger.info("Processing, please wait...")
            self.spinner.show()
            self.disable_buttons()
        else:
            self.logger.info("Processing complete.")
            self.spinner.hide()
            self.enable_buttons()

    def create_fdv(self):
        """
        A function that initiates the creation of an FDV file by setting up necessary parameters and triggering the FDV file creation process.

        Parameters:
            None

        Returns:
            None
        """
        self.on_busy_changed(True)
        depth_column = (
            "" if self.selected_depth_column == "None" else self.selected_depth_column
        )
        velocity_column = (
            ""
            if self.selected_velocity_column == "None"
            else self.selected_velocity_column
        )
        pipe_size_param = self.pipe_size_field.text() or "0"

        QTimer.singleShot(
            100,
            lambda: self.perform_fdv_creation(
                self.site_name_field.text(),
                self.pipe_shape_combo_box.currentText(),
                pipe_size_param,
                depth_column,
                velocity_column,
            ),
        )

    def perform_fdv_creation(
        self, site_name, pipe_shape, pipe_size, depth_column, velocity_column
    ):
        """
        A function that creates an FDV file by calling the backend to generate the file based on the provided site name, pipe shape, pipe size, depth column, and velocity column.
        """
        try:
            self.backend.create_fdv(
                site_name, pipe_shape, pipe_size, depth_column, velocity_column
            )
        finally:
            self.on_busy_changed(False)

    def create_rainfall(self):
        """
        A function that triggers the creation of rainfall data by calling perform_rainfall_creation with the site ID and selected rainfall column after setting the busy state.
        """
        self.on_busy_changed(True)
        QTimer.singleShot(
            100,
            lambda: self.perform_rainfall_creation(
                self.site_id, self.selected_rainfall_column
            ),
        )

    def perform_rainfall_creation(self, site_id, rainfall_column):
        """
        A function that initiates the creation of rainfall data by calling the backend to create rainfall based on the provided site ID and rainfall column after setting the busy state.

        Parameters:
            site_id: The ID of the site for which rainfall data is to be created.
            rainfall_column: The column containing rainfall data.

        Returns:
            None
        """
        try:
            self.backend.create_rainfall(site_id, rainfall_column)
        finally:
            self.on_busy_changed(False)

    def generate_rainfall_totals(self):
        """
        A function that generates rainfall totals by calling the backend to generate the totals.
        """
        self.backend.generate_rainfall_totals()

    def calculate_r3(self):
        """
        A function that calculates the R3 value based on the provided width, height, and egg type, and updates the R3 value field with the calculated value formatted to two decimal places.
        """
        width = float(self.pipe_width_field.text())
        height = float(self.pipe_height_field.text())
        egg_type = self.egg_type_combo_box.currentText()
        r3_value = self.backend.calculate_r3(width, height, egg_type)
        self.r3_value_field.setText(f"{r3_value:.2f}")

    def use_r3_in_fdv(self):
        """
        Set the pipe size in the `pipe_size_field` based on the values entered in `pipe_width_field`, `pipe_height_field`, and `r3_value_field`.
        Switch to the first tab in `tab_widget`.

        Parameters:
            None

        Returns:
            None
        """
        pipe_size = f"{self.pipe_width_field.text()},{self.pipe_height_field.text()},{self.r3_value_field.text()}"
        self.pipe_size_field.setText(pipe_size)
        self.tab_widget.setCurrentIndex(0)

    def on_back_button_clicked(self):
        """
        Emits the `back_button_clicked` signal when the back button is clicked.

        This function does not take any parameters.

        This function does not return anything.
        """
        self.back_button_clicked.emit()

    def disable_buttons(self):
        """
        Disables all the buttons on the UI.

        This function sets the enabled state of all the buttons on the UI to False.
        This is useful when you want to disable all the buttons on the UI, for example,
        when you want to prevent the user from interacting with the UI while a certain
        operation is being performed.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        self.create_fdv_button.setEnabled(False)
        self.create_rainfall_button.setEnabled(False)
        self.use_r3_button.setEnabled(False)
        self.calculate_r3_button.setEnabled(False)
        self.interim_reports_button.setEnabled(False)
        self.back_button.setEnabled(False)

    def enable_buttons(self):
        """
        Enable all buttons on the UI by setting their enabled status to True.
        """
        self.create_fdv_button.setEnabled(True)
        self.create_rainfall_button.setEnabled(True)
        self.use_r3_button.setEnabled(True)
        self.calculate_r3_button.setEnabled(True)
        self.interim_reports_button.setEnabled(True)
        self.back_button.setEnabled(True)
