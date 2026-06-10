"""
HTTP Client for Lab Data Mount Daemon (HMAC Verified Version)
"""

import hashlib
import hmac
import logging
import time
import requests

logger = logging.getLogger(__name__)

SECRET_KEY = b"00d57012a01b31f8364ebdcda42f05d15c3fd5585c69be1b8cdec1c30caa3af7"


class DaemonClient:
    def __init__(self, daemon_url, timeout=5):
        self.daemon_url = daemon_url
        self.timeout = timeout
    
    def _sign_request(self, user, tool):
        """
        Generate HMAC signature headers for the request.
        """
        timestamp = str(int(time.time()))
        message = f"{user}{tool}{timestamp}"
        signature = hmac.new(
            SECRET_KEY,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Timestamp': timestamp,
            'X-Signature': signature
        }
    
    def mount(self, user, tool, group=None, session_id=None):
        payload = {'user': user, 'tool': tool}
        if group:
            payload['group'] = group
        if session_id:
            payload['session_id'] = session_id
        
        headers = self._sign_request(user, tool)
        
        try:
            resp = requests.post(
                f"{self.daemon_url}/mount",
                json=payload,
                headers=headers,
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
    
    def unmount(self, user, tool, group=None, session_id=None):
        payload = {'user': user, 'tool': tool}
        if group:
            payload['group'] = group
        if session_id:
            payload['session_id'] = session_id
        
        headers = self._sign_request(user, tool)
        
        try:
            resp = requests.post(
                f"{self.daemon_url}/unmount",
                json=payload,
                headers=headers,
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