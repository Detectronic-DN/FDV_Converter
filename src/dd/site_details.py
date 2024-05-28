from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from src.logger.logger import logger
from src.dd.authentication import handle_authentication


def convert_to_datetime(
    epoch_timestamp: int, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[str]:
    """
    Converts the given epoch timestamp (in milliseconds) to a formatted datetime string.
    """
    try:
        seconds = epoch_timestamp // 1000
        dt = datetime.fromtimestamp(seconds)
        formatted_time = dt.strftime(format_str)
        return formatted_time
    except Exception as e:
        logger.error(f"Failed to Convert Epoch Time Stamp: {e}")
        return None


def get_site_data(
    site_id: str, username: str, password: str, base_url: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieves site data from the API using the given site ID, username, and password.
    """
    site_url = f"{base_url}GetSite?siteId={site_id}"
    response = handle_authentication(site_url, username, password)
    if response is not None:
        return response
    else:
        logger.error("Failed to Retrieve Site Data")
        return None


def site_details(
    api_url: str, username: str, password: str, site_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieves site details, including site ID, site name, start time, and end time.
    """
    site_response = get_site_data(site_id, username, password, api_url)
    channel_details_list = []

    if site_response is not None:
        site_id = site_response.get("SiteID", "")
        site_name = site_response.get("SiteName", "")
        channel_details = site_response.get("Channels", [])
        for channel in channel_details:
            channel_number = channel.get("Number", "")
            units = channel.get("Units", "")
            channel_name = channel.get("Name", "")

            channel_details_list.append(
                {
                    "site_id": site_id,
                    "site_name": site_name,
                    "channel_number": channel_number,
                    "units": units,
                    "channel_name": channel_name,
                }
            )
    else:
        logger.error("Failed to Retrieve Site Details")

    return channel_details_list


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
    site_id: str, channel_number: str, username: str, password: str, base_url: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieves channel data from the API using the specified site ID, channel number, username, and password.
    """
    channel_url = (
        f"{base_url}GetChannelDetails?{{'streamId':'{site_id}_{channel_number}'}}"
    )
    response = handle_authentication(channel_url, username, password)
    if response is not None:
        return response
    else:
        logger.error("Failed to Retrieve Channel Data")
        return None


def manage_channel_data(
    site_id: str, username: str, password: str, base_url: str
) -> List[Dict[str, Any]]:
    """
    Retrieves and processes channel data from the API using the specified site ID, username, and password.
    """
    site_data_list = site_details(base_url, username, password, site_id)
    if site_data_list:
        for site_data in site_data_list:
            channel_data = get_channel_data(
                site_id, site_data["channel_number"], username, password, base_url
            )
            if channel_data is not None:
                site_data["channel_data"] = channel_data
            else:
                logger.error(
                    f"Failed to Retrieve Channel Data for channel number {site_data['channel_number']}"
                )
    else:
        logger.error("No site data found")

    return site_data_list
