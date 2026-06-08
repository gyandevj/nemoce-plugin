import logging
import os
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class DaemonClient:
    def __init__(self):
        # Read daemon URL from environment variable or settings, default to http://127.0.0.1:5000
        self.url = os.environ.get(
            "LAB_DAEMON_URL", 
            getattr(settings, "LAB_DAEMON_URL", "http://127.0.0.1:5000")
        ).rstrip("/")
        
        self.timeout = getattr(settings, "LAB_DAEMON_TIMEOUT", 5)
        logger.debug(f"DaemonClient initialized with URL: {self.url}, timeout: {self.timeout}")

    def mount(self, user: str, tool: str) -> bool:
        """
        Sends a POST request to /mount with user and tool info.
        """
        url = f"{self.url}/mount"
        payload = {
            "user": user,
            "username": user,  # Defensive: send both 'user' and 'username'
            "tool": tool
        }
        return self._send_request(url, payload)

    def unmount(self, user: str, tool: str) -> bool:
        """
        Sends a POST request to /unmount with user and tool info.
        """
        url = f"{self.url}/unmount"
        payload = {
            "user": user,
            "username": user,  # Defensive: send both 'user' and 'username'
            "tool": tool
        }
        return self._send_request(url, payload)

    def _send_request(self, url: str, payload: dict) -> bool:
        logger.info(f"Sending POST request to {url} with payload: {payload}")
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            logger.info(f"Received response from {url}: status={response.status_code}, content={response.text}")
            if response.status_code in (200, 201, 202):
                return True
            else:
                logger.error(f"Daemon returned unexpected status code {response.status_code} for URL {url}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with daemon at {url}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error in DaemonClient calling {url}: {e}", exc_info=True)
            return False
