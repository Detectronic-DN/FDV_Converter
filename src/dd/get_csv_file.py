import os
import pandas as pd
from requests.exceptions import RequestException
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Union, Dict, Any
from src.logger.logger import logger
from src.dd.authentication import handle_authentication
from src.dd.site_details import convert_to_epoch, manage_channel_data
from src.dd.check_csv_file import check_and_fill_csv_file


def get_stream_data(
    site_id: str,
    channel_number: str,
    start_epoch: int,
    end_epoch: int,
    username: str,
    password: str,
    base_url: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves stream data from the specified site and channel within a given time range.
    """
    stream_url = f"{base_url}GetData?{{'streamId':'{site_id}_{channel_number}','start': '{start_epoch}','end': '{end_epoch}'}}"
    try:
        response = handle_authentication(stream_url, username, password)
        if response:
            return response
        else:
            logger.error("Failed to retrieve stream data")
            return None
    except RequestException as e:
        logger.error(f"Failed to retrieve stream data: {e}")
        return None


def prepare_stream_data(
    stream_data: List[dict],
) -> Tuple[List[datetime], List[Union[int, float]]]:
    """
    Processes the given stream data and extracts timestamps and values,
    using timezone-aware datetime objects.
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


def save_csv_file(df: pd.DataFrame, site_id: str, filepath: str) -> str:
    """
    Saves the DataFrame to a CSV file and returns the path to the file.
    """
    try:
        os.makedirs(filepath, exist_ok=True)
        filename = f"{site_id}.csv"
        full_path = os.path.join(filepath, filename)
        full_path = os.path.normpath(full_path)
        # Remove battery column
        if "Battery (v)" in df.columns:
            logger.info("Battery column exists, removing...")
            df.drop(columns=["Battery (v)"], inplace=True)
        df.to_csv(full_path, index=False)
        logger.info(f"CSV file saved to {full_path}")
        return full_path
    except Exception as e:
        logger.error(f"Failed to save CSV file: {e}")
        return ""


def determine_time_range(
    site_data: dict, start_time: Optional[str], end_time: Optional[str]
) -> Tuple[Optional[int], Optional[int]]:
    """
    Determines the start and end time range for data retrieval.
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
            )
            start_epoch = convert_to_epoch(start_time.strftime("%Y-%m-%d %H:%M:%S"))
            end_epoch = site_data["channel_data"]["endDate"]
        else:
            start_epoch = convert_to_epoch(start_time)
            end_epoch = convert_to_epoch(end_time)
        return start_epoch, end_epoch
    except KeyError as e:
        logger.error(f"Missing key in site data: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error determining time range: {e}")
        return None, None


def download_csv_file(
    site_id: str,
    username: str,
    password: str,
    base_url: str,
    filepath: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> Tuple[
    str,
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """
    Retrieves and processes stream data from the specified site and channel,
    and saves it to a CSV file if a filepath is provided. It returns detailed information
    about the operation outcome.

    Returns a tuple containing the site ID, site name, start time, and end time of the data included in the CSV.
    In case of an error, returns a tuple with a descriptive error message and None values for the rest.
    """
    try:
        df = pd.DataFrame(columns=["Timestamp"])
        site_data_list = manage_channel_data(site_id, username, password, base_url)
        if not site_data_list:
            logger.error("No site data available for processing.")
            return (
                "Error: No site data available for processing.",
                None,
                None,
                None,
                None,
                None,
                None,
            )

        for site_data in site_data_list:
            start_epoch, end_epoch = determine_time_range(
                site_data, start_time, end_time
            )
            if start_epoch is None or end_epoch is None:
                continue
            stream_data = get_stream_data(
                site_id,
                site_data["channel_number"],
                start_epoch,
                end_epoch,
                username,
                password,
                base_url,
            )
            if stream_data:
                datetime_values, values = prepare_stream_data(stream_data)
                channel_df = pd.DataFrame(
                    {
                        "Timestamp": datetime_values,
                        f"{site_data['channel_name'].strip()} ({site_data['units']})": values,
                    }
                )
                df = pd.merge(df, channel_df, on="Timestamp", how="outer")

        if df.empty:
            logger.error("No stream data retrieved for processing.")
            return (
                "Error: No stream data retrieved for processing.",
                None,
                None,
                None,
                None,
                None,
                None,
            )

        df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        df = df.sort_values(by="Timestamp")
        for column in df.columns:
            if column != "Timestamp":
                df[column] = df[column].astype(float).round(4)
        csv_file_path = save_csv_file(df, site_id, filepath)

        if csv_file_path:
            df, gaps, csv_file_path, interval = check_and_fill_csv_file(csv_file_path)
            start_time, end_time = df["Timestamp"].min(), df["Timestamp"].max()
            site_name = site_data_list[0]["site_name"]
            logger.info(f"CSV file successfully processed and saved: {csv_file_path}")
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
            return (
                "Error: Failed to save CSV file.",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
    except Exception as e:
        logger.error(f"Failed to process and download CSV file: {e}")
        return (
            f"Error: Exception encountered - {e}",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
