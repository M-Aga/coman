import requests
from typing import Any, Dict, Optional

class ComanAPI:
    def __init__(self, base_url: str, token: str, timeout_s: int = 12):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout_s)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.RequestException as e:
            return {"error": str(e)}

    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = requests.post(url, headers=self._headers(), json=json_data, timeout=self.timeout_s)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.RequestException as e:
            return {"error": str(e)}

    # Convenience wrappers for common Coman actions (adjust endpoints to your Core/Orchestrator)
    def info(self) -> Dict[str, Any]:
        return self.get("/v1/info")

    def process_text(self, text: str) -> Dict[str, Any]:
        return self.post("/v1/process_text", {"text": text})

    def health(self) -> Dict[str, Any]:
        return self.get("/v1/health")
