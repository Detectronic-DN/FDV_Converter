import requests
from requests.auth import HTTPDigestAuth as DigestAuth
import time
from typing import Any, Dict, Optional
from src.logger.logger import logger


def handle_authentication(
    url: str, username: str, password: str
) -> Optional[Dict[str, Any]]:
    """
    Authenticate to the API and return the JSON response.

    Args:
        url (str): The URL of the API endpoint.
        username (str): The username for Digest authentication.
        password (str): The password for Digest authentication.

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API, or None if the
            request failed after the maximum number of retries.
    """
    retries = 3
    timeout = 5
    retry_delay = 3
    max_retry_delay = 60

    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1} for authentication")
            response: requests.Response = requests.get(
                url=url, auth=DigestAuth(username, password), timeout=timeout
            )
            logger.info(f"Received response with status code {response.status_code}")

            if response.status_code == 200:
                logger.info("Authentication successful")
                return response.json()
            elif response.status_code == 403:
                logger.error(
                    "Forbidden: The user does not have the required roles or access."
                )
                break
            elif response.status_code == 404:
                logger.error("Not Found: The requested logger ID does not exist.")
                break
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", retry_delay))
                retry_delay = min(retry_after, max_retry_delay)
                logger.warning(
                    f"Too Many Requests: Retrying after {retry_delay} seconds."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            elif response.status_code == 500:
                logger.error("Internal Server Error: Retrying after a delay.")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            else:
                logger.error(
                    f"Unexpected HTTP status code received: {response.status_code}"
                )
                break
        except requests.exceptions.RequestException as e:
            logger.exception(f"API Request Exception on attempt {attempt + 1}: {e}")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

    logger.error(f"API Request Failed After {retries} Retries")
    return None
