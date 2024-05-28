from PySide6.QtCore import QObject, Signal, Slot, QSettings
from src.logger.logger import Logger


class Backend(QObject):
    loginSuccessful = Signal()
    loginFailed = Signal(str)
    logMessage = Signal(str)

    def __init__(self):
        """
        Initializes the backend, retrieves stored credentials, and sets up logging.
        """
        super().__init__()
        self.settings = QSettings("Detectronic", "FDV_UI")
        self.username = self.settings.value("username", "")
        self.password = self.settings.value("password", "")
        self.logger = Logger(__name__, emit_func=self.emit_log_message)

    def emit_log_message(self, message: str):
        """
        Emits a log message to the connected signal.

        Args:
            message (str): The log message to emit.
        """
        self.logMessage.emit(message)

    def log_info(self, message: str):
        """
        Logs an informational message.

        Args:
            message (str): The message to log.
        """
        self.logger.info(message)

    def log_error(self, message: str):
        """
        Logs an error message.

        Args:
            message (str): The message to log.
        """
        self.logger.error(message)

    @Slot(str, str)
    def save_login_details(self, username: str, password: str):
        """
        Saves the login details and emits the loginSuccessful signal.

        Args:
            username (str): The username to save.
            password (str): The password to save.
        """
        self.username = username
        self.password = password
        self.settings.setValue("username", username)
        self.settings.setValue("password", password)
        self.log_info("Credentials saved successfully.")
        self.loginSuccessful.emit()

    @Slot()
    def clear_login_details(self):
        """
        Clears the stored login details.
        """
        self.settings.remove("username")
        self.settings.remove("password")
        self.username = ""
        self.password = ""
        self.log_info("Login details cleared.")
