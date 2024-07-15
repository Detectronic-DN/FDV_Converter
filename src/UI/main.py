import sys
from PySide6.QtWidgets import QApplication

from src.UI.main_window import MainWindow
from src.logger.logger import logger


def main():
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        app.aboutToQuit.connect(main_window.cleanup)
        main_window.show()
        logger.info("Application started successfully.")
        sys.exit(app.exec())

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(-1)


if __name__ == "__main__":
    main()
