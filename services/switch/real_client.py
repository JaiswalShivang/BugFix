import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

def load_env_file():
    candidates = [
        os.path.abspath(".env"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("\"'")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

load_env_file()

class SwitchPlatformClient:
    def __init__(self):
        load_env_file()
        self.api_url = os.environ.get("SWITCH_API_URL", os.environ.get("SWITCH_ROOM_URL", "https://api.switch.dev/v1"))
        self.api_key = os.environ.get("SWITCH_API_KEY")
        self.room_id = os.environ.get("SWITCH_ROOM_ID", "bugproof")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def post_message(self, message: str, sender: str = "human") -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "ok": False,
                "remote_connected": False,
                "reason": "SWITCH_API_KEY not set in environment",
                "required_user_credentials": [
                    "SWITCH_API_KEY: API token from Flip the Switch platform",
                    "SWITCH_ROOM_ID: ID of the remote Switch room (default: bugproof)",
                    "SWITCH_API_URL: Switch platform endpoint (default: https://api.switch.dev/v1)",
                ],
            }

        url = f"{self.api_url}/rooms/{self.room_id}/messages"
        payload = json.dumps({"text": message, "sender": sender}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                return {"ok": True, "remote_connected": True, "data": data}
        except urllib.error.URLError as err:
            return {
                "ok": False,
                "remote_connected": False,
                "reason": f"Failed to connect to remote Switch platform: {str(err)}",
                "required_user_credentials": [
                    "Valid SWITCH_API_KEY",
                    "Valid SWITCH_ROOM_ID",
                ],
            }
