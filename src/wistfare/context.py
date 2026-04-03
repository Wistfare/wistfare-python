"""Execution context passed to function handlers."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class Context:
    """Context object passed to function handlers.

    Attributes:
        on_start_result: Result from the on_start hook (e.g., loaded model).
        function_id: Unique function identifier.
        invocation_id: Unique invocation identifier.
        container_id: Container running this invocation.
        timeout: Function timeout in seconds.
        env: Environment variables available to the function.
    """
    on_start_result: Any = None
    function_id: str = ""
    invocation_id: str = ""
    container_id: str = ""
    timeout: int = 300
    env: dict[str, str] | None = None
