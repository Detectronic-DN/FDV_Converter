import os
import pandas as pd
from PySide6.QtCore import QObject, Slot, Signal, QSettings, Property
from PySide6.QtWidgets import QDialog
from src.backend.timestamp import TimestampDialog  
from src.dd.get_csv_file import download_csv_file
from src.dd.check_csv_file import check_and_fill_csv_file
from src.logger.logger import Logger


class Backend(QObject):
    logMessage = Signal(str)
    siteDetailsRetrieved = Signal(str, str, str, str)
    errorOccurred = Signal(str)
    loginSuccessful = Signal()
    loginFailed = Signal(str)
    csvFileUploaded = Signal(str, str, str, str)
    finalFilePathChanged = Signal(str)
    columnsRetrieved = Signal(list)
    busyChanged = Signal(bool)  # Signal for busy state

    def __init__(self):
        """
        Initializes the backend, retrieves stored credentials, and sets up logging.
        """
        super().__init__()
        self.settings = QSettings("Detectronic", "FDV_UI")
        self.username = self.settings.value("username", "")
        self.password = self.settings.value("password", "")
        self.base_url = "https://www.detecdata-en.com/API2.ashx/"
        self._final_file_path = ""
        self._busy = False  # Busy state
        self.logger = Logger(__name__, emit_func=self.emit_log_message)
        self.site_id = ""
        self.site_name = ""
        self.interval = ""

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

    @Property(bool, notify=busyChanged)  # Busy property
    def busy(self):
        return self._busy

    @busy.setter
    def busy(self, value):
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    @Slot(str, str)
    def save_login_details(self, username: str, password: str):
        """Save user login details to settings."""
        self.username = username
        self.password = password
        self.settings.setValue("username", username)
        self.settings.setValue("password", password)
        self.log_info("Credentials saved successfully.")
        self.loginSuccessful.emit()

    @Slot()
    def clear_login_details(self):
        """Clear user login details from settings."""
        self.settings.remove("username")
        self.settings.remove("password")
        self.username = ""
        self.password = ""
        self.log_info("Login details cleared.")

    @Slot(str, str)
    def download_csv_file(self, site_id: str, folderpath: str):
        """Download CSV file for the given site ID."""
        self.busy = True  # Set busy before starting the operation
        try:
            self.log_info(f"Initiating download for site {site_id}")
            result = download_csv_file(
                site_id, self.username, self.password, self.base_url, folderpath
            )

            if result[0].startswith("Error"):
                self.log_error(result[0])
                self.errorOccurred.emit(result[0])
            else:
                (
                    site_id,
                    site_name,
                    start_timestamp,
                    end_timestamp,
                    csv_filepath,
                    gaps,
                    interval,
                ) = result
                start_time = pd.to_datetime(start_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                end_time = pd.to_datetime(end_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                self.final_file_path = csv_filepath
                self.site_id = site_id
                self.site_name = site_name
                self.interval = interval
                self.siteDetailsRetrieved.emit(site_id, site_name, start_time, end_time)
                self.log_info(f"There are {gaps} gaps in the CSV File.")
                self.log_info(f"CSV file downloaded and saved to {csv_filepath}")
        except Exception as e:
            error_message = f"Exception occurred while downloading CSV file: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False  # Reset busy after the operation

    @Slot(str)
    def upload_csv_file(self, filepath: str):
        """Upload and process the given CSV file."""
        self.busy = True  # Set busy before starting the operation
        try:
            self.log_info(f"Loading file from {filepath}")
            self._final_file_path = filepath

            # Check and fill CSV file
            df, gaps, file_path, interval = check_and_fill_csv_file(
                self._final_file_path
            )
            self.log_info(f"There are {gaps} gaps in the data.")
            self.log_info(f"CSV File checked and gaps filled successfully")

            # Extract site ID and site name from the file name
            file_name = os.path.basename(file_path)
            site_id = file_name.split(".")[0]
            site_name = site_id

            self.site_id = site_id
            self.site_name = site_name
            self.interval = interval

            # Process the DataFrame to extract timestamps
            time_col = df.columns[0]
            df[time_col] = pd.to_datetime(df[time_col])
            df.sort_values(by=time_col, inplace=True)
            start_timestamp = df[time_col].min().strftime("%Y-%m-%d %H:%M:%S")
            end_timestamp = df[time_col].max().strftime("%Y-%m-%d %H:%M:%S")

            # Emit signal with site details
            self.siteDetailsRetrieved.emit(
                site_id, site_name, start_timestamp, end_timestamp
            )
            self.columnsRetrieved.emit(df.columns.tolist())  # Emit columns retrieved
            self.final_file_path = file_path
            self.log_info(f"Final file path set to {self.final_file_path}")
        except Exception as e:
            error_message = f"Exception occurred while uploading file: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False  # Reset busy after the operation

    @Slot()
    def retrieveColumns(self):
        """Retrieve columns from the currently selected CSV file."""
        csv_file_name = self.final_file_path
        if csv_file_name:
            try:
                df = pd.read_csv(csv_file_name)
                columns = df.columns.tolist()
                self.columnsRetrieved.emit(columns)
                self.log_info(f"Columns retrieved: {columns}")
            except Exception as e:
                error_message = f"Error retrieving columns: {str(e)}"
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)
        else:
            error_message = "No CSV file selected."
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)

    @Slot(str, str, result=list)
    def edit_timestamps(self, start_timestamp, end_timestamp):
        """Edit the start and end timestamps."""
        self.log_info(
            f"Editing timestamps: Start = {start_timestamp}, End = {end_timestamp}"
        )
        dialog = TimestampDialog(start_timestamp, end_timestamp)
        if dialog.exec() == QDialog.Accepted:
            new_start_timestamp, new_end_timestamp = dialog.get_timestamps()
            self.log_info(
                f"New timestamps: Start = {new_start_timestamp}, End = {new_end_timestamp}"
            )
            self.modified_start_timestamp = new_start_timestamp
            self.modified_end_timestamp = new_end_timestamp
            self.modify_csv_file()
            return [new_start_timestamp, new_end_timestamp]
        else:
            self.log_info("Timestamp editing cancelled")
            return [start_timestamp, end_timestamp]

    def modify_csv_file(self):
        """Modify the CSV file based on the new timestamps."""
        try:
            self.log_info("Modifying CSV file")

            # Ensure the file path is set
            if not self.final_file_path:
                error_message = "No file selected for modification."
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)
                return

            # Read the CSV file
            df = pd.read_csv(self.final_file_path)
            self.log_info(f"Loaded file from {self.final_file_path}")

            # Convert the timestamp column to datetime
            time_col = df.columns[0]
            df[time_col] = pd.to_datetime(df[time_col])

            # Apply the timestamp mask
            mask = (df[time_col] >= pd.to_datetime(self.modified_start_timestamp)) & (
                df[time_col] <= pd.to_datetime(self.modified_end_timestamp)
            )
            modified_df = df.loc[mask]

            # Save the modified file with a new name
            filename, extension = os.path.splitext(
                os.path.basename(self.final_file_path)
            )
            modified_filepath = os.path.join(
                os.path.dirname(self.final_file_path), f"{filename}_modified{extension}"
            )
            modified_df.to_csv(modified_filepath, index=False)

            # Update the file path and emit the signal
            self.final_file_path = modified_filepath
            self.finalFilePathChanged.emit(modified_filepath)
            self.log_info(f"Modified file saved to {modified_filepath}")
        except Exception as e:
            error_message = f"Exception occurred while modifying CSV file: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
