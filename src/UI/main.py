import os
import sys

sys.path.append(os.getcwd())
from PySide6.QtWidgets import QApplication

from src.logger.logger import logger
from src.backend.backend import Backend
from src.UI.main_window import MainWindow


def main():
    try:
        app = QApplication(sys.argv)

        backend = Backend()

        # Create the main window and pass the backend to it
        main_window = MainWindow()

        # Connect the aboutToQuit signal to the backend cleanup method
        app.aboutToQuit.connect(backend.clear_login_details)

        main_window.show()

        logger.info("Application started successfully.")
        sys.exit(app.exec())

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(-1)


if __name__ == "__main__":
    main()
