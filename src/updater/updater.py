import sys
import subprocess
from PySide6.QtWidgets import QMessageBox

from src.logger.logger import logger


class GitUpdater:
    BRANCH = "master"

    @classmethod
    def check_for_updates(cls):
        try:
            with open("version.txt", "r") as f:
                current_version = f.read().strip()

            subprocess.run(["git", "fetch", "origin", cls.BRANCH], check=True)

            current_commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
            )
            latest_commit = (
                subprocess.check_output(["git", "rev-parse", f"origin/{cls.BRANCH}"])
                .decode()
                .strip()
            )

            if current_commit != latest_commit:
                # Get the latest version from the remote version.txt
                latest_version = (
                    subprocess.check_output(
                        ["git", "show", f"origin/{cls.BRANCH}:version.txt"]
                    )
                    .decode()
                    .strip()
                )

                msg = QMessageBox()
                msg.setWindowTitle("Update Available")
                msg.setText(
                    f"A new version ({latest_version}) is available. You are currently on version {current_version}. Would you like to update?"
                )
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                if msg.exec() == QMessageBox.Yes:
                    return cls.perform_update()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
        return False

    @classmethod
    def perform_update(cls):
        try:
            subprocess.run(["git", "pull", "origin", cls.BRANCH], check=True)
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
            )

            QMessageBox.information(
                None,
                "Update Successful",
                "The application has been updated. Please restart to apply changes.",
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Update failed: {e}")
            QMessageBox.warning(
                None,
                "Update Failed",
                f"The update process encountered an error: {e}\nPlease try again later or contact support.",
            )
        except Exception as e:
            logger.error(f"Unexpected error during update: {e}")
            QMessageBox.warning(
                None,
                "Update Failed",
                f"An unexpected error occurred: {e}\nPlease try again later or contact support.",
            )
        return False
