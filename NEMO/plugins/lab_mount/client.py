"""
HTTP Client for Lab Data Mount Daemon (No HMAC - Simple Version)
"""

import logging
import requests

logger = logging.getLogger(__name__)


class DaemonClient:
    def __init__(self, daemon_url, timeout=5):
        self.daemon_url = daemon_url
        self.timeout = timeout
    
    def mount(self, user, tool, session_id=None):
        payload = {'user': user, 'tool': tool}
        if session_id:
            payload['session_id'] = session_id
        
        try:
            resp = requests.post(
                f"{self.daemon_url}/mount",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code in (200, 201):
                logger.info(f"Mounted {user} on {tool}")
                return True
            logger.error(f"Mount failed: {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"Mount error: {e}")
            return False
    
    def unmount(self, user, tool, session_id=None):
        payload = {'user': user, 'tool': tool}
        if session_id:
            payload['session_id'] = session_id
        
        try:
            resp = requests.post(
                f"{self.daemon_url}/unmount",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                logger.info(f"Unmounted {user} from {tool}")
                return True
            logger.error(f"Unmount failed: {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"Unmount error: {e}")
            return False