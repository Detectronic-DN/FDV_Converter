import os
import re
from typing import Tuple, Dict, Optional

import keyring
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, QSettings
from PySide6.QtWidgets import QDialog

from src.FDV.FDV_converter import FDV_conversion
from src.FDV.FDV_rainfall_converter import perform_R_conversion
from src.calculator.r3calculator import R3Calculator
from src.backend.timestamp import TimestampDialog
from src.Interiem_reports.Interim_Class import InterimReportGenerator
from src.dd.dd_class import Dd
from src.logger.logger import Logger


class Backend(QObject):
    logMessage = Signal(str)
    errorOccurred = Signal(str)
    loginSuccessful = Signal()
    loginFailed = Signal(str)
    busyChanged = Signal(bool)
    siteDetailsRetrieved = Signal(str, str, str, str)
    columnsRetrieved = Signal(list)
    finalFilePathChanged = Signal(str)
    fdvCreated = Signal(str)
    fdvError = Signal(str)
    rainfallCreated = Signal(str)
    rainfallError = Signal(str)
    interimReportCreated = Signal(str)

    def __init__(self):
        """
        Initializes the backend, retrieves stored credentials, and sets up logging.
        """
        super().__init__()
        self.modified_end_timestamp = None
        self.modified_start_timestamp = None
        self._final_file_path = None
        self.interval = None
        self.site_name = None
        self.site_id = None
        self.final_file_path = None
        self.settings = QSettings("Detectronic", "FDV_UI")
        self.service_name = "FDV Converter"
        self.username = self.settings.value("username", "")
        self.password = self.settings.value("password", "")
        self.base_url = "https://www.detecdata-en.com/API2.ashx/"
        self._busy = False
        self.logger = Logger(__name__, emit_func=self.emit_log_message)
        self.dd_instance = None
        self.column_map = {}
        self.monitor_type = None

    def emit_log_message(self, message: str) -> None:
        """
        Emits a log message to the connected signal.

        Args:
            message (str): The log message to emit.
        """
        self.logMessage.emit(message)

    def log_info(self, message: str) -> None:
        """
        Logs an informational message.

        Args:
            message (str): The message to log.
        """
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """
        Logs an error message.

        Args:
            message (str): The message to log.
        """
        self.logger.error(message)

    @property
    def busy(self) -> bool:
        return self._busy

    @busy.setter
    def busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    @property
    def final_file_path(self) -> str:
        return self._final_file_path

    @final_file_path.setter
    def final_file_path(self, value: str) -> None:
        if self._final_file_path != value:
            self._final_file_path = value
            self.finalFilePathChanged.emit(value)

    @Slot(str, str)
    def save_login_details(self, username: str, password: str) -> None:
        """
        Save user login details to settings.

        Args:
            username (str): Username.
            password (str): Password.
        """
        self.username = username
        self.password = password
        self.settings.setValue("username", username)
        self.settings.setValue("password", password)
        keyring.set_password(self.service_name, "username", username)
        keyring.set_password(self.service_name, "password", password)
        self.log_info("Credentials saved successfully.")
        self.dd_instance = Dd(self.username, self.password, self.base_url)
        self.loginSuccessful.emit()

    @Slot()
    def clear_login_details(self) -> None:
        """Clear user login details from settings."""
        self.settings.remove("username")
        self.settings.remove("password")
        self.username = ""
        self.password = ""
        self.log_info("Login details cleared.")

    @Slot()
    def get_login_details(self) -> Tuple[str | None, str | None]:
        """
        Retrieves the login details from keyring.

        Returns:
            tuple: A tuple containing the username and password.
        """
        try:
            username = keyring.get_password(self.service_name, "username")
            password = keyring.get_password(self.service_name, "password")
            return username, password
        except Exception as e:
            self.logger.error(f"Failed to retrieve login details: {e}")
            return None, None

    @Slot(str, str)
    def download_csv_file(self, site_id: str, folder_path: str) -> None:
        """
        Download CSV file for the given site ID.

        Args:
            site_id (str): Site ID.
            folder_path (str): Folder path to save the CSV file.
        """
        self.busy = True
        try:
            self.emit_log_message(
                f"Downloading CSV for site {site_id} to {folder_path}"
            )
            result = self.dd_instance.download_csv_file(site_id, folder_path)

            if result[0].startswith("Error"):
                raise ValueError(result[0])

            (
                site_id,
                site_name,
                start_timestamp,
                end_timestamp,
                csv_filepath,
                gaps,
                interval,
            ) = result
            start_time = pd.to_datetime(start_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            end_time = pd.to_datetime(end_timestamp).strftime("%Y-%m-%d %H:%M:%S")

            self.final_file_path = csv_filepath
            self.site_id = site_id
            self.site_name = site_name
            self.interval = interval

            self.siteDetailsRetrieved.emit(site_id, site_name, start_time, end_time)
            self.log_info(f"There are {gaps} gaps in the CSV File.")
            self.log_info(f"CSV file downloaded and saved to {csv_filepath}")

        except ValueError as ve:
            self.log_error(str(ve))
            self.errorOccurred.emit(str(ve))
        except Exception as e:
            error_message = f"Unexpected error occurred while downloading CSV file: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False

    @staticmethod
    def identify_timestamp_column(df: pd.DataFrame) -> str:
        """
        Identifies the timestamp column using common timestamp keywords.

        Args:
            df (pd.DataFrame): The DataFrame containing the data.

        Returns:
            str: The name of the timestamp column.
        """
        timestamp_keywords = [
            "timestamp",
            "Time Stamp",
            "time",
            "TimeStamp",
            "Timestamp",
        ]
        for col in df.columns:
            if any(keyword.lower() in col.lower() for keyword in timestamp_keywords):
                return col
        raise ValueError("Timestamp column not found.")

    def get_column_names_and_indices(
        self, file_name: str, df: pd.DataFrame
    ) -> Dict[str, Tuple[str, int]]:
        """
        Extract and validate column names and their indices based on the monitor type identified from the file name.

        Args:
            file_name (str): Name of the file to identify the monitor type.
            df (pd.DataFrame): DataFrame containing the CSV data.

        Returns:
            dict: A dictionary with the required columns and their indices.
        """
        column_mapping = {}

        # Define patterns for dynamic column matching
        depth_pattern = re.compile(r"\d+_\d+\|Depth\|m")
        flow_pattern = re.compile(r"\d+_\d+\|Flow\|l/s")
        velocity_pattern = re.compile(r"\d+_\d+\|Velocity\|m/s")
        rainfall_pattern = re.compile(r"Rainfall")

        # Identify the timestamp column
        timestamp_col = self.identify_timestamp_column(df)
        column_mapping["timestamp"] = (timestamp_col, df.columns.get_loc(timestamp_col))

        if file_name.startswith("DM"):
            self.monitor_type = "Depth"
            # Depth Monitor
            depth_col = next(
                (col for col in df.columns if depth_pattern.match(col)), None
            )
            if depth_col:
                column_mapping["depth"] = (depth_col, df.columns.get_loc(depth_col))
            else:
                raise ValueError("Required depth column not found for Depth Monitor.")
        elif file_name.startswith("FM"):
            self.monitor_type = "Flow"
            # Flow Monitor
            flow_col = next(
                (col for col in df.columns if flow_pattern.match(col)), None
            )
            depth_col = next(
                (col for col in df.columns if depth_pattern.match(col)), None
            )
            velocity_col = next(
                (col for col in df.columns if velocity_pattern.match(col)), None
            )

            if flow_col and depth_col and velocity_col:
                column_mapping["flow"] = (flow_col, df.columns.get_loc(flow_col))
                column_mapping["depth"] = (depth_col, df.columns.get_loc(depth_col))
                column_mapping["velocity"] = (
                    velocity_col,
                    df.columns.get_loc(velocity_col),
                )
            else:
                raise ValueError("Required columns not found for Flow Monitor.")
        elif file_name.startswith("RG"):
            self.monitor_type = "Rainfall"
            # Rainfall Gauge Monitor
            rainfall_col = next(
                (col for col in df.columns if rainfall_pattern.match(col)), None
            )
            if rainfall_col:
                column_mapping["rainfall"] = (
                    rainfall_col,
                    df.columns.get_loc(rainfall_col),
                )
            else:
                raise ValueError(
                    "Required rainfall column not found for Rainfall Gauge Monitor."
                )
        else:
            raise ValueError("Unknown monitor type based on file name.")

        return column_mapping

    @Slot(str)
    def upload_csv_file(self, filepath: str) -> None:
        """
        Upload and process the given CSV file.

        Args:
            filepath (str): File path of the CSV file to upload.
        """
        self.busy = True
        try:
            self.log_info(f"Loading file from {filepath}")
            self._final_file_path = filepath

            # Check and fill CSV file
            result = self.dd_instance.check_and_fill_csv_file(self._final_file_path)
            if result is None:
                raise ValueError("Failed to check and fill the CSV file.")

            df, gaps, file_path, interval = result
            self.log_info(f"There are {gaps} gaps in the data.")
            self.log_info("CSV file checked and gaps filled successfully")

            # Extract site ID and site name from the file name
            file_name = os.path.basename(file_path)
            site_id = file_name.split(".")[0]
            site_name = site_id

            self.site_id = site_id
            self.site_name = site_name
            self.interval = interval

            time_col = self.identify_timestamp_column(df)

            # Process the DataFrame to extract timestamps
            df[time_col] = pd.to_datetime(df[time_col])
            df.sort_values(by=time_col, inplace=True)
            start_timestamp = df[time_col].min().strftime("%Y-%m-%d %H:%M:%S")
            end_timestamp = df[time_col].max().strftime("%Y-%m-%d %H:%M:%S")

            # Emit signal with site details
            self.siteDetailsRetrieved.emit(
                site_id, site_name, start_timestamp, end_timestamp
            )
            self.columnsRetrieved.emit(df.columns.tolist())
            self.final_file_path = file_path
            self.log_info(f"Final file path set to {self.final_file_path}")
        except ValueError as ve:
            self.log_error(str(ve))
            self.errorOccurred.emit(str(ve))
        except Exception as e:
            error_message = f"Exception occurred while uploading file: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False

    @Slot()
    def retrieve_columns(self) -> None:
        """
        Retrieve columns and their indices from the currently selected CSV file based on the monitor type.
        """
        if self.final_file_path:
            try:
                df = pd.read_csv(self.final_file_path)
                file_name = os.path.basename(self.final_file_path)
                self.column_map = self.get_column_names_and_indices(file_name, df)

                columns_with_indices = {
                    key: (val[0], val[1]) for key, val in self.column_map.items()
                }

                self.columnsRetrieved.emit(
                    [f"{val[0]}" for val in self.column_map.values()]
                )
                self.log_info(f"Columns retrieved: {columns_with_indices}")

            except ValueError as ve:
                error_message = f"ValueError retrieving columns: {str(ve)}"
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)

            except Exception as e:
                error_message = f"Error retrieving columns: {str(e)}"
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)

        else:
            error_message = "No CSV file selected."
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)

    @Slot(str, str, result=list)
    def edit_timestamps(self, start_timestamp: str, end_timestamp: str) -> list:
        """
        Edit the start and end timestamps.

        Args:
            start_timestamp (str): Original start timestamp.
            end_timestamp (str): Original end timestamp.

        Returns:
            list: Updated start and end timestamps.
        """
        self.log_info(
            f"Editing timestamps: Start = {start_timestamp}, End = {end_timestamp}"
        )
        dialog = TimestampDialog(start_timestamp, end_timestamp)
        if dialog.exec() == QDialog.DialogCode.Accepted:
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

    def modify_csv_file(self) -> None:
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
            file_name = os.path.basename(self.final_file_path)

            # Convert the timestamp column to datetime
            time_col = self.identify_timestamp_column(df)
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
        self,
        site_name: str,
        pipe_type: str,
        pipe_size_param: str,
        depth_col: Optional[str],
        velocity_col: Optional[str],
    ) -> None:
        """
        Create an FDV file.

        Args:
            site_name (str): Site name.
            pipe_type (str): Pipe type.
            pipe_size_param (str): Pipe size parameter.
            depth_col (str): Depth column name.
            velocity_col (str): Velocity column name.
        """
        self.busy = True
        try:
            csv_file_name = self.final_file_path
            df = pd.read_csv(csv_file_name)
            time_col = self.identify_timestamp_column(df)
            df[time_col] = pd.to_datetime(df[time_col])
            df.sort_values(by=time_col, inplace=True)
            df.reset_index(drop=True, inplace=True)
            start_date = df[time_col].min()
            end_date = df[time_col].max()
            interval = pd.to_timedelta(self.interval)

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
            self.busy = False

    @Slot(str, str)
    def create_rainfall(self, site_name: str, rainfall_col: str) -> None:
        """
        Create a rainfall file.

        Args:
            site_name (str): Site name.
            rainfall_col (str): Rainfall column name.
        """
        self.busy = True
        try:
            csv_file_name = self.final_file_path
            df = pd.read_csv(csv_file_name)

            time_col = self.identify_timestamp_column(df)
            df[time_col] = pd.to_datetime(df[time_col])
            df.sort_values(by=time_col, inplace=True)
            df.reset_index(drop=True, inplace=True)
            start_date = df[time_col].min()
            end_date = df[time_col].max()
            interval = pd.to_timedelta(self.interval)

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
            self.busy = False

    @Slot(float, float, str, result=float)
    def calculate_r3(self, width: float, height: float, egg_form: str) -> float:
        """
        Calculate the R3 value based on given dimensions and egg form.

        Args:
            width (float): Width of the pipe.
            height (float): Height of the pipe.
            egg_form (str): Egg form type.

        Returns:
            float: Calculated R3 value.
        """
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

    @Slot()
    def create_interim_reports(self) -> None:
        """Create interim reports."""
        self.busy = True
        try:
            self.log_info("Creating interim reports")
            if not self.final_file_path:
                error_message = "No CSV file selected."
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)
                return

            generator = InterimReportGenerator(self)
            report_df, values_df, daily_summary = generator.generate_report()

            output_dir = os.path.join(os.path.dirname(self.final_file_path), "interim_reports")
            os.makedirs(output_dir, exist_ok=True)

            self.interimReportCreated.emit(f"Saving interim report to {output_dir}")

            # Save interim report and daily summary to Excel
            excel_file_path = os.path.join(
                output_dir,
                f"{os.path.basename(self.final_file_path).split('.')[0]}_interim_report.xlsx",
            )
            with pd.ExcelWriter(excel_file_path) as writer:
                values_df.to_excel(writer, sheet_name="Values", index=False)
                report_df.to_excel(writer, sheet_name="Summaries", index=False)
                daily_summary.to_excel(writer, sheet_name="Daily", index=False)

            generator.save_interim_files(report_df, daily_summary, output_dir)
            self.interimReportCreated.emit(
                f"Interim report created successfully at {output_dir}"
            )
        except Exception as e:
            error_message = f"Exception occurred while creating interim report: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False
