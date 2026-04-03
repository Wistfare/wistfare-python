"""Wistfare API client for programmatic function invocation."""

import httpx
from typing import Any


class WistfareClient:
    """Client for interacting with the Wistfare Functions API."""

    def __init__(self, token: str, base_url: str = "https://api.wistfare.com"):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=300.0,
        )

    def create_function(self, **kwargs) -> dict:
        resp = self._client.post("/v1/functions", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    def list_functions(self) -> list[dict]:
        resp = self._client.get("/v1/functions")
        resp.raise_for_status()
        return resp.json().get("functions", [])

    def get_function(self, function_id: str) -> dict:
        resp = self._client.get(f"/v1/functions/{function_id}")
        resp.raise_for_status()
        return resp.json()

    def delete_function(self, function_id: str) -> None:
        resp = self._client.delete(f"/v1/functions/{function_id}")
        resp.raise_for_status()

    def deploy(self, function_id: str, code_archive: bytes) -> dict:
        resp = self._client.post(
            f"/v1/functions/{function_id}/deploy",
            content=code_archive,
            headers={"Content-Type": "application/octet-stream"},
        )
        resp.raise_for_status()
        return resp.json()

    def invoke(self, function_id: str, payload: Any = None) -> dict:
        resp = self._client.post(
            f"/v1/functions/{function_id}/invoke",
            json=payload or {},
        )
        resp.raise_for_status()
        return resp.json()

    def enqueue(self, function_id: str, payload: Any = None) -> dict:
        resp = self._client.post(
            f"/v1/functions/{function_id}/enqueue",
            json=payload or {},
        )
        resp.raise_for_status()
        return resp.json()

    def get_task(self, function_id: str, task_id: str) -> dict:
        resp = self._client.get(f"/v1/functions/{function_id}/tasks/{task_id}")
        resp.raise_for_status()
        return resp.json()

    def get_metrics(self, function_id: str) -> dict:
        resp = self._client.get(f"/v1/functions/{function_id}/metrics")
        resp.raise_for_status()
        return resp.json()

    def scale(self, function_id: str, desired_instances: int) -> dict:
        resp = self._client.post(
            f"/v1/functions/{function_id}/scale",
            json={"desired_instances": desired_instances},
        )
        resp.raise_for_status()
        return resp.json()

    def gpu_types(self) -> list[dict]:
        resp = self._client.get("/v1/functions/gpu-types")
        resp.raise_for_status()
        return resp.json().get("gpu_types", [])

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
