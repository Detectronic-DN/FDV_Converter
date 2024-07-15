import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.UI.main_window import MainWindow
from src.logger.logger import logger
from src.updater.updater import GitUpdateChecker

# Constants
UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000
INITIAL_UPDATE_CHECK_DELAY = 5000


def main():
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        app.aboutToQuit.connect(main_window.cleanup)
        main_window.show()
        QTimer.singleShot(
            INITIAL_UPDATE_CHECK_DELAY, GitUpdateChecker.check_for_updates
        )
        update_timer = QTimer()
        update_timer.timeout.connect(GitUpdateChecker.check_for_updates)
        update_timer.start(UPDATE_CHECK_INTERVAL)

        logger.info("Application started successfully.")
        sys.exit(app.exec())

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(-1)


if __name__ == "__main__":
    main()
