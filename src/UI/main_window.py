from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QTextEdit,
    QSplitter,
)

from src.UI.fdv_page import FDVPage
from src.UI.login_page import LoginPage
from src.UI.site_details_page import SiteDetailsPage
from src.backend.backend import Backend
from src.logger.logger import Logger


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        """
        Initializes the MainWindow with UI components and navigation.
        """
        super().__init__()
        self.setWindowTitle("FDV App")
        self.setGeometry(100, 100, 640, 480)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.logger = Logger(__name__)

        main_layout = QVBoxLayout(central_widget)

        # Create a splitter to separate the main content and log display
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Create a stacked widget for navigation
        self.stack = QStackedWidget()
        self.backend = Backend()

        # Create pages
        self.site_details_page = SiteDetailsPage(self.backend, self.stack)
        self.login_page = LoginPage(self.backend)

        # Add pages to the stack
        self.stack.addWidget(self.site_details_page)
        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.site_details_page)

        # Add the stack to the splitter
        splitter.addWidget(self.stack)

        # Create and set up the log widget
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)  # Limit the height of the log display

        # Add the log widget to the splitter
        splitter.addWidget(self.log_widget)

        # Add the splitter to the main layout
        main_layout.addWidget(splitter)

        # Connect the Logger's log signal to the log widget
        Logger.connect_log_signal(self.update_log_display)

        # Connect signals to slots
        self.site_details_page.login_requested.connect(self.show_login_page)
        self.site_details_page.open_login_page.connect(self.show_login_page)
        self.login_page.login_successful.connect(self.show_site_details_page)
        self.login_page.navigate_to_site_details.connect(self.show_site_details_page)
        self.site_details_page.continue_to_next.connect(self.show_fdv_page)

        # Apply the light theme stylesheet
        self.setStyleSheet(
            """
            QWidget {
              background-color: #ffffff;
              color: #000000;
            }
        """
        )
        self.setWindowIcon(QIcon("icons/calculation.ico"))
        self.show()

    @Slot(str)
    def update_log_display(self, message: str) -> None:
        """
        Updates the log display with new log messages.
        """
        self.log_widget.append(message)

    def show_site_details_page(self) -> None:
        """
        Shows the site details page.
        """
        self.stack.setCurrentWidget(self.site_details_page)
        username, _ = self.backend.get_login_details()
        self.site_details_page.update_username(username)
        self.set_log_visibility(True)

    def show_login_page(self) -> None:
        """
        Shows the login page.
        """
        if self.login_page not in [
            self.stack.widget(i) for i in range(self.stack.count())
        ]:
            self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)
        self.set_log_visibility(False)

    def show_fdv_page(self) -> None:
        """
        Shows the FDV page with the necessary parameters.
        """
        fdv_page = FDVPage(
            self.backend,
            self.site_details_page.filePath,
            self.site_details_page.siteId,
            self.site_details_page.startTimestamp,
            self.site_details_page.endTimestamp,
        )
        self.stack.addWidget(fdv_page)
        self.stack.setCurrentWidget(fdv_page)
        fdv_page.back_button_clicked.connect(self.show_site_details_page)
        self.set_log_visibility(True)

    def closeEvent(self, event) -> None:
        """
        Handles the close event to ensure all threads are properly closed.
        """
        self.cleanup()
        event.accept()

    def cleanup(self) -> None:
        """
        Cleans up any resources and threads.
        """
        self.backend.clear_login_details()  # Ensure login details are cleared
        self.site_details_page.close_threads()

    def set_log_visibility(self, visible: bool) -> None:
        """
        Sets the visibility of the log widget.
        """
        self.log_widget.setVisible(visible)
