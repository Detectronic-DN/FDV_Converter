import os
import re
from typing import Tuple, Dict, Optional

import keyring
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, QSettings
from PySide6.QtWidgets import QDialog

from src.FDV.FDV_converter import fdv_conversion
from src.FDV.FDV_rainfall_converter import perform_r_conversion
from src.calculator.r3calculator import r3_calculator
from src.backend.timestamp import TimestampDialog
from src.Interiem_reports.Interim_Class import InterimReportGenerator
from src.Interiem_reports.rainfall_calcuations import RainfallTotalsGenerator
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
    rainfallTotalsCreated = Signal(str)

    def __init__(self):
        """
        Initializes the backend, retrieves stored credentials, and sets up logging.
        """
        super().__init__()
        self.channel_id = None
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
        self.custom_column_mapping = {
            "depth": ["Depth", "Water Level", "Level", "level"],
            "rainfall": ["Rainfall", "rainfall"],
            "flow": ["Flow", "flow"],
        }

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
    def get_login_details(self) -> Tuple[Optional[str], Optional[str]]:
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
    ) -> Dict[str, list]:
        """
        Extract and validate column names and their indices based on the monitor type identified from the file name.
        Store site_id and channel_id directly in instance variables.

        Args:
            file_name (str): Name of the file to identify the monitor type.
            df (pd.DataFrame): DataFrame containing the CSV data.

        Returns:
            dict: A dictionary with the required columns and their indices.
        """
        column_mapping = {
            "timestamp": [],
            "flow": [],
            "depth": [],
            "velocity": [],
            "rainfall": [],
        }

        # Define patterns for dynamic column matching
        depth_pattern = re.compile(r"(\d+)_(\d+)\|.*(Depth|Level)\|m")
        flow_pattern = re.compile(r"(\d+)_(\d+)\|.*Flow\|l/s")
        velocity_pattern = re.compile(r"(\d+)_(\d+)\|.*Velocity\|m/s")
        rainfall_pattern = re.compile(r"(\d+)_(\d+)\|.*Rainfall\|mm")

        # Identify the timestamp column
        timestamp_col = self.identify_timestamp_column(df)
        column_mapping["timestamp"].append(
            (timestamp_col, df.columns.get_loc(timestamp_col), None, None)
        )

        def extract_columns(pattern, df_columns, custom_key=None):
            """
            Extracts columns based on a given pattern and a set of DataFrame columns.

            Args:
                pattern: A regular expression pattern to match against the columns.
                df_columns: The columns of the DataFrame to match against.
                custom_key: A key to customize the column matching process (default is None).

            Returns:
                A list of tuples containing matched columns, their indices, and additional extracted groups.
            """
            matches = [
                (pattern.match(col), col, df.columns.get_loc(col))
                for col in df_columns
                if pattern.match(col)
            ]
            if not matches and custom_key and custom_key in self.custom_column_mapping:
                matches = [
                    (None, col, df.columns.get_loc(col))
                    for col in df_columns
                    if any(
                        alias.lower() in col.lower()
                        for alias in self.custom_column_mapping[custom_key]
                    )
                ]
            return [
                (
                    match[1],
                    match[2],
                    match[0].group(1) if match[0] else None,
                    match[0].group(2) if match[0] else None,
                )
                for match in matches
            ]

        # Extract columns for specific types
        for col_type, pattern in [
            ("flow", flow_pattern),
            ("depth", depth_pattern),
            ("velocity", velocity_pattern),
            ("rainfall", rainfall_pattern),
        ]:
            cols = extract_columns(pattern, df.columns, custom_key=col_type)
            if cols:
                column_mapping[col_type] = cols

        # Determine monitor type based on file name or column presence
        if file_name.startswith("DM"):
            self.monitor_type = "Depth"
        elif file_name.startswith("FM"):
            self.monitor_type = "Flow"
        elif file_name.startswith("RG"):
            self.monitor_type = "Rainfall"
        else:
            # If file name doesn't indicate monitor type, determine from columns
            if column_mapping["rainfall"]:
                self.monitor_type = "Rainfall"
            elif column_mapping["flow"]:
                self.monitor_type = "Flow"
            elif column_mapping["depth"]:
                self.monitor_type = "Depth"
            else:
                raise ValueError("Unable to determine monitor type from columns")

        self.log_info(f"Monitor type: {self.monitor_type}")

        # Set site_id and channel_id based on the determined monitor type
        if self.monitor_type == "Depth" and column_mapping["depth"]:
            depth_col_match = depth_pattern.match(column_mapping["depth"][0][0])
            if depth_col_match:
                self.site_id = depth_col_match.group(1)
                self.channel_id = depth_col_match.group(2)
            else:
                self.site_id = "Unknown"
                self.channel_id = "Unknown"
                self.log_warning(
                    "Could not extract site and channel info from depth/level column name"
                )
        elif self.monitor_type == "Flow" and column_mapping["flow"]:
            self.site_id = column_mapping["flow"][0][2]
            self.channel_id = column_mapping["flow"][0][3]
        elif self.monitor_type == "Rainfall" and column_mapping["rainfall"]:
            self.site_id = column_mapping["rainfall"][0][2]
            self.channel_id = column_mapping["rainfall"][0][3]
        else:
            self.site_id = "Unknown"
            self.channel_id = "Unknown"
            self.log_warning("Could not determine site and channel info")

        return column_mapping

    @Slot()
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
            result = Dd.check_and_fill_csv_file(self._final_file_path)
            if result is None:
                raise ValueError("Failed to check and fill the CSV file.")

            df, gaps, file_path, interval = result
            self.log_info(f"There are {gaps} gaps in the data.")

            self.site_id = None
            self.site_name = None

            # Extract site ID and site name from the file name
            file_name = os.path.basename(file_path)
            site_name = file_name.split(".")[0]

            # Split the file name by common separators
            name_parts = re.split(r"[-_\s]", site_name)

            # Try to identify site ID and name
            self.site_id = None
            self.site_name = site_name  # Default to full file name if we can't parse it

            for part in name_parts:
                if part.isdigit():
                    self.site_id = part
                    break  # Assume the first number is the site ID

            if self.site_id:
                # If we found a site ID, everything after it is potentially the site name
                site_name_parts = name_parts[name_parts.index(self.site_id) + 1:]
                if site_name_parts:
                    self.site_name = " ".join(site_name_parts)
            else:
                # If we didn't find a numeric site ID, use the whole name as site name
                self.site_name = site_name
            self.interval = interval

            self.column_map = self.get_column_names_and_indices(file_name, df)
            if self.site_id == "Unknown":
                # If we couldn't extract from column name, try to get from file name
                for part in name_parts:
                    if part.isdigit():
                        self.site_id = part
                        break

            # If we have a site_id, use it to construct the site_name
            if self.site_id != "Unknown":
                site_name_parts = [part for part in name_parts if part != self.site_id]
                self.site_name = (
                    " ".join(site_name_parts)
                    if site_name_parts
                    else f"Site {self.site_id}"
                )
            else:
                # If we still don't have a site_id, use the whole filename as site_name
                self.site_name = site_name
                self.log_warning(
                    f"Could not determine site ID. Using full filename as site name: {self.site_name}"
                )

            # Emit signal with site details
            time_col = self.identify_timestamp_column(df)
            df[time_col] = pd.to_datetime(df[time_col])
            df.sort_values(by=time_col, inplace=True)
            start_timestamp = df[time_col].min().strftime("%Y-%m-%d %H:%M:%S")
            end_timestamp = df[time_col].max().strftime("%Y-%m-%d %H:%M:%S")
            self.siteDetailsRetrieved.emit(
                self.site_id, self.site_name, start_timestamp, end_timestamp
            )
            self.columnsRetrieved.emit(df.columns.tolist())
            self.final_file_path = file_path
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

                # Create a simplified version for logging
                simplified_column_map = {}
                for key, value in self.column_map.items():
                    if value:  # Only include non-empty lists
                        simplified_column_map[key] = [
                            col[0] for col in value
                        ]  # Include all column names for each type

                # Keep the original column_map structure for the application
                columns_list = []
                for key, value in self.column_map.items():
                    for col_info in value:
                        columns_list.append(col_info[0])

                self.columnsRetrieved.emit(columns_list)

                # Log the simplified version
                self.log_info(f"Columns retrieved: {simplified_column_map}")

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

            null_readings = fdv_conversion(
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
                null_readings = perform_r_conversion(
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

            r3_value = r3_calculator(width, height, egg_form_value)
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
            summaries_df, values_df, daily_summary = generator.generate_report()

            output_dir = os.path.join(
                os.path.dirname(self.final_file_path), "final_report"
            )
            generator.save_final_report(
                summaries_df, values_df, daily_summary, output_dir
            )
            self.interimReportCreated.emit(
                f"Final report created successfully at {output_dir}"
            )
        except Exception as e:
            error_message = f"Exception occurred while creating interim report: {e}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False

    @Slot()
    def generate_rainfall_totals(self):
        self.busy = True
        try:
            self.log_info("Generating rainfall totals")
            if not self.final_file_path:
                error_message = "No CSV file selected."
                self.log_error(error_message)
                self.errorOccurred.emit(error_message)
                return

            generator = RainfallTotalsGenerator(self)
            daily_totals, weekly_totals = generator.generate_totals()

            output_dir = os.path.join(os.path.dirname(self.final_file_path), "rainfall_totals")
            generator.save_totals(daily_totals, weekly_totals, output_dir)
            self.rainfallTotalsCreated.emit(f"Rainfall totals created successfully at {output_dir}")
        except Exception as e:
            error_message = f"Exception occurred while generating rainfall totals: {str(e)}"
            self.log_error(error_message)
            self.errorOccurred.emit(error_message)
        finally:
            self.busy = False
