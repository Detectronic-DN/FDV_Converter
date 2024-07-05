from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget

from src.UI.fdv_page import FDVPage
from src.UI.login_page import LoginPage
from src.UI.site_details_page import SiteDetailsPage
from src.backend.backend import Backend


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

        central_layout = QVBoxLayout(central_widget)

        # Create a stacked widget for navigation
        self.stack = QStackedWidget()
        self.backend = Backend()

        self.login_page = LoginPage(self.backend)
        self.site_details_page = SiteDetailsPage(self.backend, self.stack)

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.site_details_page)

        central_layout.addWidget(self.stack)

        # Connect signals to slots
        self.login_page.navigate_to_site_details.connect(self.show_site_details_page)
        self.site_details_page.back_button_clicked.connect(self.show_login_page)
        self.site_details_page.continue_to_next.connect(self.show_fdv_page)

        # Apply the light theme stylesheet
        self.apply_stylesheet("./light_theme_stylesheet.qss")
        self.show()

    def apply_stylesheet(self, stylesheet_path):
        """
        Applies the stylesheet to the application.
        """
        with open(stylesheet_path, "r") as file:
            self.setStyleSheet(file.read())

    def show_site_details_page(self) -> None:
        """
        Shows the site details page.
        """
        self.stack.setCurrentWidget(self.site_details_page)

    def show_login_page(self) -> None:
        """
        Shows the login page.
        """
        self.stack.setCurrentWidget(self.login_page)

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

    def close_event(self, event) -> None:
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
