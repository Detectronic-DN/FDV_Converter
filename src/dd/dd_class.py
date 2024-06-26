import os
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Union

import pandas as pd
import pendulum
import pendulum.parsing
import pendulum.parsing.exceptions
import requests
from pandas import DataFrame
from requests.auth import HTTPDigestAuth as DigestAuth
from requests.exceptions import RequestException

from src.logger.logger import Logger, logger


def map_column_names_to_index(dataframe: pd.DataFrame) -> Dict[str, int]:
    """
    Maps the column names to their respective indices in the given DataFrame.
    """
    return {col: idx for idx, col in enumerate(dataframe.columns)}


def identify_timestamp_column(
    column_mapping: Dict[str, int]
) -> Tuple[Optional[str], Optional[int]]:
    """
    Identifies the index of the timestamp column using the column mapping.
    """
    timestamp_keywords = ["timestamp", "Time Stamp", "time", "TimeStamp", "Timestamp"]
    for col, idx in column_mapping.items():
        if any(keyword in col.lower() for keyword in timestamp_keywords):
            return col, idx
    return None, None


class Dd:
    def __init__(self, username: str, password: str, base_url: str):
        """
        Initialize the DD_Api class with the given username, password, and base URL.

        :param username: The username for Digest authentication.
        :param password: The password for Digest authentication.
        :param base_url: The base URL for the API.
        """
        self.username = username
        self.password = password
        self.base_url = base_url
        self.logger = Logger(__name__)
        self.site_id: Optional[str] = None
        self.site_name: Optional[str] = None
        self.channel_details_list: List[Dict[str, Any]] = []

    def _handle_authentication(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate to the API and return the JSON response.

        :param endpoint: The specific endpoint of the API.
        :return: The JSON response from the API, or None if the request failed after the maximum number of retries.
        """
        retries = 3
        timeout = 5
        retry_delay = 3
        max_retry_delay = 60

        for attempt in range(retries):
            try:
                self.logger.info(f"Attempt {attempt + 1} for authentication")
                response = requests.get(
                    url=endpoint,
                    auth=DigestAuth(self.username, self.password),
                    timeout=timeout,
                )
                self.logger.info(
                    f"Received response with status code {response.status_code}"
                )

                if response.status_code == 200:
                    self.logger.info("Authentication successful")
                    return response.json()
                elif response.status_code == 403:
                    self.logger.error(
                        "Forbidden: The user does not have the required roles or access."
                    )
                    break
                elif response.status_code == 404:
                    self.logger.error(
                        "Not Found: The requested logger ID does not exist."
                    )
                    break
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", retry_delay))
                    retry_delay = min(retry_after, max_retry_delay)
                    self.logger.warning(
                        f"Too Many Requests: Retrying after {retry_delay} seconds."
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                elif response.status_code == 500:
                    self.logger.error("Internal Server Error: Retrying after a delay.")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                else:
                    self.logger.error(
                        f"Unexpected HTTP status code received: {response.status_code}"
                    )
                    break
            except RequestException as e:
                self.logger.exception(
                    f"API Request Exception on attempt {attempt + 1}: {e}"
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

        self.logger.error(f"API Request Failed After {retries} Retries")
        return None

    def make_site_data_request(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Make a request using the credentials and siteId.

        :param site_id: The ID of the site to retrieve data for.
        :return: The JSON response from the API, or None if the request failed.
        """
        site_url = f"{self.base_url}GetSite?siteId={site_id}"
        return self._handle_authentication(site_url)

    def map_site_details(self, site_id: str) -> bool:
        """
        Retrieves site details, including site ID, site name, start time, and end time.

        :param site_id: The ID of the site to retrieve details for.
        :return: True if site details were successfully retrieved and mapped, False otherwise.
        """
        site_response = self.make_site_data_request(site_id)
        if site_response:
            self.site_id = site_response.get("SiteID", "")
            self.site_name = site_response.get("SiteName", "")
            self.channel_details_list = [
                {
                    "channel_number": channel.get("Number", ""),
                    "units": channel.get("Units", ""),
                    "channel_name": channel.get("Name", ""),
                }
                for channel in site_response.get("Channels", [])
            ]
            return True
        else:
            self.logger.error("Failed to Retrieve Site Details")
            return False

    @staticmethod
    def convert_to_datetime(
        epoch_timestamp: int, format_str: str = "%Y-%m-%d %H:%M:%S"
    ) -> Optional[str]:
        """
        Converts the given epoch timestamp (in milliseconds) to a formatted datetime string.
        """
        try:
            seconds = epoch_timestamp // 1000
            dt = datetime.fromtimestamp(seconds)
            return dt.strftime(format_str)
        except Exception as e:
            logger.error(f"Failed to Convert Epoch Time Stamp: {e}")
            return None

    @staticmethod
    def convert_to_epoch(
        date_string: str, date_format: str = "%Y-%m-%d %H:%M:%S"
    ) -> Optional[int]:
        """
        Converts a given date string to its corresponding epoch time.
        """
        try:
            dt = datetime.strptime(date_string, date_format)
            return int(dt.replace(tzinfo=timezone.utc).timestamp()) * 1000
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting date to epoch: {e}")
            return None

    def get_channel_data(
        self, site_id: str, channel_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves channel data from the API using the specified site ID and channel number.

        :param site_id: The ID of the site.
        :param channel_number: The number of the channel.
        :return: The JSON response from the API, or None if the request failed.
        """
        channel_url = f"{self.base_url}GetChannelDetails?{{'streamId':'{site_id}_{channel_number}'}}"
        return self._handle_authentication(channel_url)

    def manage_channel_data(self, site_id: str) -> bool:
        """
        Retrieves and processes channel data from the API using the specified site ID.

        :param site_id: The ID of the site.
        :return: True if channel data was successfully retrieved and processed, False otherwise.
        """
        if self.map_site_details(site_id):
            for channel in self.channel_details_list:
                channel_data = self.get_channel_data(site_id, channel["channel_number"])
                if channel_data:
                    channel["channel_data"] = channel_data
                else:
                    self.logger.error(
                        f"Failed to Retrieve Channel Data for channel number {channel['channel_number']}"
                    )
            return True
        else:
            self.logger.error("No site data found")
            return False

    def get_stream_data(
        self, site_id: str, channel_number: str, start_epoch: int, end_epoch: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves stream data from the specified site and channel within a given time range.

        :param site_id: The ID of the site.
        :param channel_number: The number of the channel.
        :param start_epoch: The start time in epoch milliseconds.
        :param end_epoch: The end time in epoch milliseconds.
        :return: The JSON response from the API, or None if the request failed.
        """
        stream_url = (
            f"{self.base_url}GetData?{{'streamId':'{site_id}_{channel_number}',"
            f"'start': '{start_epoch}','end': '{end_epoch}'}}"
        )
        return self._handle_authentication(stream_url)

    @staticmethod
    def prepare_stream_data(
        stream_data: List[Dict[str, Any]]
    ) -> Tuple[List[datetime], List[Union[int, float]]]:
        """
        Processes the given stream data and extracts timestamps and values.

        :param stream_data: The stream data to process.
        :return: A tuple of lists containing datetime objects and corresponding values.
        """
        datetime_values: List[datetime] = []
        values: List[Union[int, float]] = []
        for item in stream_data:
            try:
                timestamp = datetime.fromtimestamp(item["ts"] / 1000, tz=timezone.utc)
                datetime_values.append(timestamp)
                values.append(item["v"])
            except KeyError as e:
                logger.error(f"Missing key in stream data item: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing stream data: {e}")
        return datetime_values, values

    def determine_time_range(
        self,
        site_data: Dict[str, Any],
        start_time: Optional[str],
        end_time: Optional[str],
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Determines the start and end time range for data retrieval.

        :param site_data: The site data containing channel details.
        :param start_time: The start time as a string.
        :param end_time: The end time as a string.
        :return: A tuple containing the start and end times in epoch milliseconds.
        """
        try:
            if not start_time or not end_time:
                start_time = datetime(
                    site_data["channel_data"]["year"],
                    site_data["channel_data"]["month"],
                    site_data["channel_data"]["day"],
                    site_data["channel_data"]["hour"],
                    site_data["channel_data"]["minute"],
                    site_data["channel_data"]["second"],
                ).strftime("%Y-%m-%d %H:%M:%S")
                start_epoch = self.convert_to_epoch(start_time)
                end_epoch = site_data["channel_data"]["endDate"]
            else:
                start_epoch = self.convert_to_epoch(start_time)
                end_epoch = self.convert_to_epoch(end_time)
            return start_epoch, end_epoch
        except KeyError as e:
            self.logger.error(f"Missing key in site data: {e}")
            return None, None
        except Exception as e:
            self.logger.error(f"Unexpected error determining time range: {e}")
            return None, None

    @staticmethod
    def calculate_interval(timestamps: pd.Series) -> Optional[pd.Timedelta]:
        """Calculate the most common interval between timestamps.

        Args:
            timestamps (pd.Series): A pandas Series of timestamps.

        Returns:
            Optional[pd.Timedelta]: The most common interval or None if it cannot be calculated.
        """
        logger.info("Calculating the most common interval between timestamps.")

        if timestamps.empty:
            logger.warning("Timestamp series is empty.")
            return None

        try:
            # Ensure timestamps are sorted
            timestamps = timestamps.sort_values()

            # Calculate differences
            intervals = timestamps.diff().dropna()

            if intervals.empty:
                logger.warning("No valid intervals found between timestamps.")
                return None

            # Calculate the mode
            mode_interval = intervals.mode()

            if mode_interval.empty:
                logger.warning("Could not determine a mode interval.")
                return None

            result = mode_interval.iloc[0]
            logger.info(f"Most common interval calculated: {result}")
            return result

        except Exception as e:
            logger.error(f"Error calculating interval: {e}")
            return None

    @staticmethod
    def save_csv_file(df: pd.DataFrame, site_name: str, filepath: str) -> Optional[str]:
        """
        Saves the DataFrame to a CSV file and returns the path to the file.

        :param df: The DataFrame to save.
        :param site_name: The name of the site.
        :param filepath: The directory to save the file in.
        :return: The full path to the saved CSV file, or None if an error occurred.
        """
        try:
            os.makedirs(filepath, exist_ok=True)
            filename = f"{site_name}.csv"
            full_path = os.path.join(filepath, filename)
            df.to_csv(full_path, index=False)
            logger.info(f"CSV file saved to {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Failed to save CSV file: {e}")
            return None

    @staticmethod
    def try_parsing_date(text: str) -> Optional[pendulum.DateTime]:
        """Try to parse a date string using Pendulum's automatic parsing."""
        try:
            return pendulum.parse(text, strict=False)
        except (ValueError, pendulum.parsing.exceptions.ParserError):
            return None

    @staticmethod
    def parse_dates(date_series: pd.Series) -> pd.Series:
        """Parse dates with mixed formats using Pendulum's automatic parsing."""
        try:
            parsed_dates = date_series.apply(Dd.try_parsing_date)
            # Convert Pendulum objects to pandas Timestamp for compatibility
            return parsed_dates.apply(lambda x: pd.Timestamp(x.to_iso8601_string()) if x else pd.NaT)
        except Exception as e:
            logger.error(f"Error parsing dates: {e}")
            return pd.Series([pd.NaT] * len(date_series))

    @staticmethod
    def fill_gaps(df: pd.DataFrame, interval: pd.Timedelta) -> Tuple[DataFrame, int]:
        """Fill gaps in the dataframe based on the most common interval."""
        try:
            column_mapping = map_column_names_to_index(df)
            timestamp_column, _ = identify_timestamp_column(column_mapping)
            if timestamp_column is None:
                raise ValueError("Timestamp column not found.")

            full_range = pd.date_range(
                start=df[timestamp_column].min(),
                end=df[timestamp_column].max(),
                freq=interval,
            )
            logger.info(
                f"Full date range generated from {df[timestamp_column].min()} to {df[timestamp_column].max()}."
            )
            original_len = len(df)
            df.set_index(timestamp_column, inplace=True)
            df = df.reindex(full_range)
            df.index.name = timestamp_column
            df.reset_index(inplace=True)
            filled_len = len(df)
            gap_count = filled_len - original_len

            logger.info(f"{gap_count} gaps filled in the dataframe.")
            return df, gap_count
        except Exception as e:
            logger.error(f"Error filling gaps: {e}")
            return df, 0

    def check_and_fill_csv_file(
        self, filepath: str
    ) -> tuple[DataFrame | DataFrame, int, str, timedelta] | None:
        """Check if a CSV file exists and fill any gaps based on the most common interval."""
        try:
            self.logger.info(f"Checking if file exists: {filepath}")
            if not os.path.exists(filepath):
                self.logger.error("File does not exist.")
                return None

            # Read the file based on extension
            self.logger.info(f"Reading the file: {filepath}")
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath)
                self.logger.info("File read as CSV.")
            elif filepath.endswith(".xlsx"):
                df = pd.read_excel(filepath)
                self.logger.info("File read as Excel.")
            else:
                self.logger.error("Unsupported file format.")
                return None

            # Parse dates in the first column
            self.logger.info("Parsing dates in the dataframe.")
            df[df.columns[0]] = self.parse_dates(df[df.columns[0]])
            self.logger.info("Dates parsed successfully.")

            # Ensure timestamps are sorted
            self.logger.info("Sorting timestamps in the dataframe.")
            df.sort_values(by=df.columns[0], inplace=True)

            # Calculate interval and fill gaps
            interval = self.calculate_interval(df[df.columns[0]])
            if interval is not None:
                df, gaps_count = self.fill_gaps(df, interval)
                self.logger.info(f"There are {gaps_count} gaps in the data.")
                df.to_csv(filepath, index=False)
                self.logger.info(f"CSV file updated and saved to {filepath}")
                return df, gaps_count, filepath, interval
            else:
                self.logger.error("Failed to calculate the interval, cannot fill gaps.")
                return None
        except Exception as e:
            self.logger.error(f"An error occurred while processing the file: {e}")
            return None

    def download_csv_file(
        self,
        site_id: str,
        filepath: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Optional[Tuple]:
        """
        Retrieves and processes stream data from the specified site and channel,
        and saves it to a CSV file if a filepath is provided. It returns detailed information
        about the operation outcome.

        Returns a tuple containing the site ID, site name, start time, and end time of the data included in the CSV.
        In case of an error, returns a tuple with a descriptive error message and None values for the rest.
        """
        try:
            df = pd.DataFrame(columns=["Timestamp"])
            self.site_id = site_id
            if not self.manage_channel_data(site_id):
                self.logger.error("No site data available for processing.")
                return None

            for channel in self.channel_details_list:
                start_epoch, end_epoch = self.determine_time_range(
                    channel, start_time, end_time
                )
                if start_epoch is None or end_epoch is None:
                    continue
                stream_data = self.get_stream_data(
                    site_id, channel["channel_number"], start_epoch, end_epoch
                )
                if stream_data:
                    datetime_values, values = self.prepare_stream_data(stream_data)
                    channel_df = pd.DataFrame(
                        {
                            "Timestamp": datetime_values,
                            f"{site_id}_{channel['channel_number']}|"
                            f"{channel['channel_name'].strip()}|"
                            f"{channel['units']}": values,
                        }
                    )
                    df = pd.merge(df, channel_df, on="Timestamp", how="outer")

            if df.empty:
                self.logger.error("No stream data retrieved for processing.")
                return None

            df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            df = df.sort_values(by="Timestamp")
            for column in df.columns:
                if column != "Timestamp":
                    df[column] = df[column].astype(float).round(4)
            sn = self.site_name.split(" ")[0] if self.site_name is not None else "site"
            df = df.loc[:, ~df.columns.str.contains("Battery")]
            csv_file_path = self.save_csv_file(df, sn, filepath)

            if csv_file_path:
                result = self.check_and_fill_csv_file(csv_file_path)
                if result:
                    df, gaps, csv_file_path, interval = result
                    start_time, end_time = df["Timestamp"].min(), df["Timestamp"].max()
                    site_name = self.site_name
                    self.logger.info(
                        f"CSV file successfully processed and saved: {csv_file_path}"
                    )
                    return (
                        site_id,
                        site_name,
                        start_time,
                        end_time,
                        csv_file_path,
                        gaps,
                        interval,
                    )
                else:
                    self.logger.error("Failed to check and fill the file")
                    return None
            else:
                self.logger.error("Failed to save the file")
                return None
        except Exception as e:
            self.logger.error(f"Failed to process and download CSV file: {e}")
            return None
