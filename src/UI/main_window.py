from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
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
        self.site_details_page = SiteDetailsPage(self.backend)

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.site_details_page)

        central_layout.addWidget(self.stack)

        self.login_page.navigate_to_site_details.connect(self.show_site_details_page)
        self.site_details_page.back_button_clicked.connect(self.show_login_page)

        self.show()

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
