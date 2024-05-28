import os
import sys
sys.path.append(os.getcwd())
from PySide6.QtWidgets import QApplication
from src.UI.main_window import MainWindow


def main() -> None:
    """
    Entry point for the application.
    """
    app = QApplication(sys.argv)

    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
