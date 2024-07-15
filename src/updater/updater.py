import sys
import subprocess
from PySide6.QtWidgets import QMessageBox


class gitUpdater:

    @classmethod
    def check_for_updates(cls):
        try:
            subprocess.run(["git", "fetch"], check=True)
            current_commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
            )
            lasted_commit = (
                subprocess.check_output(["git", "rev-parse", "FETCH_HEAD"])
                .decode()
                .strip()
            )

            if current_commit != lasted_commit:
                msg = QMessageBox()
                msg.setWindowTitle("Update Available")
                msg.setText("A new version is available. Would you like to update?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                if msg.exec() == QMessageBox.Yes:
                    cls.perform_update()
                    return True
        except Exception as e:
            print(f"Error checking for updates: {e}")
        return False

    @classmethod
    def perform_update(cls):
        try:
            subprocess.run(["git", "pull"], check=True)
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
            )

            QMessageBox.information(
                None,
                "Update Successful",
                "The application has been updated. Please restart to apply changes.",
            )
            sys.exit()

        except Exception as e:
            print(f"Error updating: {e}")
