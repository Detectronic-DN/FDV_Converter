import os
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, QSettings, Property
from PySide6.QtWidgets import QDialog
from src.backend.timestamp import TimestampDialog
from src.dd.get_csv_file import download_csv_file
from src.dd.check_csv_file import check_and_fill_csv_file
from src.logger.logger import Logger
from src.FDV.FDV_converter import FDV_conversion
from src.Interiem_reports.interim_reports import (
    create_interim_report,
    calculate_daily_summary,
    save_interim_files,
)
from src.FDV.FDV_rainfall_converter import perform_R_conversion
from src.calculator.r3calculator import R3Calculator


class Backend(QObject):
    logMessage = Signal(str)
    siteDetailsRetrieved = Signal(str, str, str, str)
    errorOccurred = Signal(str)
    loginSuccessful = Signal()
    loginFailed = Signal(str)
    csvFileUploaded = Signal(str, str, str, str)
    finalFilePathChanged = Signal(str)
    columnsRetrieved = Signal(list)
    busyChanged = Signal(bool)
    fdvCreated = Signal(str)
    fdvError = Signal(str)
    interimReportCreated = Signal(str)
    rainfallCreated = Signal(str)
    rainfallError = Signal(str)

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
        self.busyChanged.emit(True)
        try:
            self.emit_log_message(f"Downloading CSV for site {site_id} to {folderpath}")
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
            self.busyChanged.emit(False)

    @Slot(str)
    def upload_csv_file(self, filepath: str):
        """Upload and process the given CSV file."""
        self.busyChanged.emit(True)
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
            self.busyChanged.emit(False)

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

    @Slot(str, str, str, str, str)
    def create_fdv(
        self, site_name, pipe_type, pipe_size_param, depth_col, velocity_col
    ):
        """Create an FDV file."""
        self.busy = True  # Set busy before starting the operation
        try:
            csv_file_name = self.final_file_path
            df = pd.read_csv(csv_file_name)
            columns = df.columns
            df[columns[0]] = pd.to_datetime(df[columns[0]])
            df.sort_values(by=columns[0], inplace=True)
            df.reset_index(drop=True, inplace=True)
            start_date = df[columns[0]].min()
            end_date = df[columns[0]].max()
            interval = self.interval

            # Handle "None" option for columns
            if depth_col == "None":
                depth_col = None
            if velocity_col == "None":
                velocity_col = None

            # Create output directory and file path
            output_dir = os.path.join(os.path.dirname(csv_file_name), "FDV")
            os.makedirs(output_dir, exist_ok=True)
            output_file_name = os.path.join(output_dir, f"{site_name}.fdv")

            null_readings = FDV_conversion(
                csv_file_name,
                output_file_name,
                site_name,
                start_date,
                end_date,
                interval,
                pipe_type,
                pipe_size_param,
                depth_col,
                velocity_col,
            )
            self.fdvCreated.emit(
                f"FDV conversion completed. Null readings: {null_readings}"
            )
            self.log_info(f"FDV file created: {output_file_name}")
        except Exception as e:
            self.fdvError.emit(str(e))
            self.log_error(f"Error creating FDV file: {e}")
        finally:
            self.busy = False  # Reset busy after the operation

    @Slot()
    def create_interim_reports(self):
        """Create interim reports."""
        self.busy = True  # Set busy before starting the operation
        try:
            csv_file_name = self.final_file_path
            if not csv_file_name:
                error_message = "No CSV file selected."
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)
                return

            self.log_info(f"Loading file from {csv_file_name}")
            df = pd.read_csv(csv_file_name)
            columns = df.columns
            time_column = columns[0]
            flow_column = columns[1]
            df[time_column] = pd.to_datetime(df[time_column])
            df.sort_values(by=time_column, inplace=True)
            df.reset_index(drop=True, inplace=True)

            interval = self.interval
            interval = int(interval.total_seconds())

            report_df, values_df = create_interim_report(
                df, flow_column, time_column, interval
            )
            daily_summary = calculate_daily_summary(df, time_column, flow_column)

            output_dir = os.path.join(os.path.dirname(csv_file_name), "interim_reports")
            os.makedirs(output_dir, exist_ok=True)

            self.interimReportCreated.emit(f"Saving interim report to {output_dir}")

            # Save interim report and daily summary to Excel
            excel_file_path = os.path.join(
                output_dir,
                f"{os.path.basename(csv_file_name).split('.')[0]}_interim_report.xlsx",
            )
            with pd.ExcelWriter(excel_file_path) as writer:
                values_df.to_excel(writer, sheet_name="Values", index=False)
                report_df.to_excel(writer, sheet_name="Summaries", index=False)
                daily_summary.to_excel(writer, sheet_name="Daily", index=False)

            save_interim_files(report_df, daily_summary, output_dir)
            self.interimReportCreated.emit(
                f"Interim report created successfully at {output_dir}"
            )
        except Exception as e:
            error_message = f"Exception occurred while creating interim report: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False  # Reset busy after the operation

    @Property(str, notify=finalFilePathChanged)
    def final_file_path(self):
        return self._final_file_path

    @final_file_path.setter
    def final_file_path(self, value):
        if self._final_file_path != value:
            self._final_file_path = value
            self.finalFilePathChanged.emit(value)

    @Slot(str, str)
    def create_rainfall(self, site_name: str, rainfall_col: str):
        """Create a rainfall file."""
        self.busy = True  # Set busy before starting the operation
        try:
            csv_file_name = self.final_file_path
            df = pd.read_csv(csv_file_name)
            columns = df.columns
            df[columns[0]] = pd.to_datetime(df[columns[0]])
            df.sort_values(by=columns[0], inplace=True)
            df.reset_index(drop=True, inplace=True)
            start_date = df[columns[0]].min()
            end_date = df[columns[0]].max()
            interval = self.interval

            # Handle "None" option for rainfall column
            if rainfall_col == "None":
                error_message = "Rainfall column cannot be 'None'."
                self.log_error(error_message)
                self.rainfallError.emit(error_message)
                return

            output_dir = os.path.join(os.path.dirname(csv_file_name), "rainfall")
            os.makedirs(output_dir, exist_ok=True)
            output_file_name = os.path.join(output_dir, f"{site_name}.r")

            try:
                null_readings = perform_R_conversion(
                    csv_file_name,
                    output_file_name,
                    site_name,
                    start_date,
                    end_date,
                    interval,
                    rainfall_col,
                )
                self.rainfallCreated.emit(
                    f"Rainfall conversion completed. Null readings: {null_readings}"
                )
                self.log_info(f"Rainfall file created successfully: {output_file_name}")
            except Exception as e:
                self.rainfallError.emit(str(e))
                self.log_error(f"Error creating rainfall file: {e}")
        except Exception as e:
            error_message = f"Exception occurred while creating rainfall file: {e}"
            self.log_error(error_message)
            self.rainfallError.emit(error_message)
        finally:
            self.busy = False  # Reset busy after the operation

    @Slot(float, float, str, result=float)
    def calculate_r3(self, width: float, height: float, egg_form: str) -> float:
        """Calculate the R3 value based on given dimensions and egg form."""
        try:
            if egg_form == "Egg Type 1":
                egg_form_value = 1
            elif egg_form == "Egg Type 2":
                egg_form_value = 2
            else:
                raise ValueError(f"Unknown egg form: {egg_form}")

            r3_value = R3Calculator(width, height, egg_form_value)
            return r3_value
        except Exception as e:
            self.log_error(f"Error calculating R3 value: {str(e)}")
            return -1.0
