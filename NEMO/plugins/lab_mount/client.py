"""
HTTP Client for Lab Data Mount Daemon (HMAC Verified Version - Hierarchical ID-based)

Mount/unmount requests now include account_id and project_id so the daemon
mounts only the specific project folder the user checked into, rather than
the entire groups directory.
"""

import hashlib
import hmac
import logging
import time
import requests

logger = logging.getLogger(__name__)

SECRET_KEY = b"00d57012a01b31f8364ebdcda42f05d15c3fd5585c69be1b8cdec1c30caa3af7"


class DaemonClient:
    def __init__(self, daemon_url, cert=None, verify=True, timeout=5):
        """
        :param daemon_url: The base URL of the daemon (e.g., https://127.0.0.1:5000)
        :param cert: Path to client certificate file or a tuple (cert_path, key_path)
        :param verify: Path to CA bundle to verify daemon's certificate, or boolean
        :param timeout: Request timeout in seconds
        """
        self.daemon_url = daemon_url
        self.cert = cert
        self.verify = verify
        self.timeout = timeout

    def mount(self, user_id, tool, account_id, project_id, session_id=None):
        """
        Request the daemon to mount the session directories for user_id on tool.
        """
        payload = {
            'user_id': user_id,
            'tool': tool,
            'account_id': account_id,
            'project_id': project_id,
        }
        if session_id:
            payload['session_id'] = session_id

        try:
            resp = requests.post(
                f"{self.daemon_url}/mount",
                json=payload,
                cert=self.cert,
                verify=self.verify,
                timeout=self.timeout
            )
            if resp.status_code in (200, 201):
                logger.info(
                    f"Successfully requested mount for user ID {user_id} on {tool} "
                    f"(account={account_id}, project={project_id})"
                )
                return True
            logger.error(f"Mount request failed: {resp.status_code} - {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Mount request error: {e}")
            return False

    def unmount(self, user_id, tool, account_id, project_id, session_id=None):
        """
        Request the daemon to unmount the session directories for user_id on tool.
        """
        payload = {
            'user_id': user_id,
            'tool': tool,
            'account_id': account_id,
            'project_id': project_id,
        }
        if session_id:
            payload['session_id'] = session_id

        try:
            resp = requests.post(
                f"{self.daemon_url}/unmount",
                json=payload,
                cert=self.cert,
                verify=self.verify,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                logger.info(
                    f"Successfully requested unmount for user ID {user_id} from {tool} "
                    f"(account={account_id}, project={project_id})"
                )
                return True
            logger.error(f"Unmount request failed: {resp.status_code} - {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Unmount request error: {e}")
            return False

    def initialize_user(self, user_id):
        """Trigger directory and quota initialization for a newly created user."""
        payload = {'user_id': user_id, 'tool': 'system'}

        try:
            resp = requests.post(
                f"{self.daemon_url}/init_user",
                json=payload,
                cert=self.cert,
                verify=self.verify,
                timeout=self.timeout
            )
            if resp.status_code in (200, 201):
                logger.info(f"Successfully requested user folder initialization for user ID {user_id}")
                return True
            logger.error(f"User folder initialization request failed: {resp.status_code} - {resp.text}")
            return False
        except Exception as e:
            logger.error(f"User folder initialization request error: {e}")
            return False