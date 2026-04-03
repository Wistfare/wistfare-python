"""Function decorators for defining serverless GPU functions."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class FunctionConfig:
    """Configuration for a serverless function."""
    name: str
    invoke_type: str  # function, endpoint, task_queue, schedule
    cpu: int = 1  # cores
    memory: str = "512Mi"
    gpu: str = ""
    gpu_count: int = 0
    image: Any = None
    keep_warm: int = 60
    max_instances: int = 10
    min_instances: int = 0
    timeout: int = 300
    concurrency: int = 1
    schedule_cron: str = ""
    handler: Callable | None = None
    on_start_handler: Callable | None = None


def _parse_memory(memory: str) -> int:
    """Parse memory string to MB. E.g., '512Mi' -> 512, '2Gi' -> 2048."""
    memory = memory.strip()
    if memory.endswith("Gi"):
        return int(float(memory[:-2]) * 1024)
    elif memory.endswith("Mi"):
        return int(memory[:-2])
    elif memory.endswith("G"):
        return int(float(memory[:-1]) * 1024)
    elif memory.endswith("M"):
        return int(memory[:-1])
    else:
        return int(memory)


def _create_decorator(invoke_type: str, **kwargs):
    """Create a function decorator with the given configuration."""
    def decorator(fn: Callable) -> Callable:
        config = FunctionConfig(
            name=kwargs.get("name") or fn.__name__,
            invoke_type=invoke_type,
            cpu=kwargs.get("cpu", 1),
            memory=kwargs.get("memory", "512Mi"),
            gpu=kwargs.get("gpu", ""),
            gpu_count=kwargs.get("gpu_count", 1 if kwargs.get("gpu") else 0),
            image=kwargs.get("image"),
            keep_warm=kwargs.get("keep_warm", 60),
            max_instances=kwargs.get("max_instances", 10),
            min_instances=kwargs.get("min_instances", 0),
            timeout=kwargs.get("timeout", 300),
            concurrency=kwargs.get("concurrency", 1),
            schedule_cron=kwargs.get("schedule_cron", kwargs.get("cron", "")),
        )
        config.handler = fn

        fn._wistfare_config = config

        def on_start(start_fn: Callable = None):
            """Register an on_start hook that runs once per container boot."""
            def inner(start_fn_inner):
                config.on_start_handler = start_fn_inner
                return start_fn_inner
            if start_fn is not None:
                return inner(start_fn)
            return inner

        fn.on_start = on_start

        return fn
    return decorator


def endpoint(name: str | None = None, **kwargs):
    """Decorator for HTTP endpoint functions with auto-scaling."""
    if callable(name):
        fn = name
        return _create_decorator("endpoint")(fn)
    kwargs["name"] = name
    kwargs.setdefault("keep_warm", 180)
    return _create_decorator("endpoint", **kwargs)


def function(name: str | None = None, **kwargs):
    """Decorator for direct invocation functions."""
    if callable(name):
        fn = name
        return _create_decorator("function")(fn)
    kwargs["name"] = name
    return _create_decorator("function", **kwargs)


def task_queue(name: str | None = None, **kwargs):
    """Decorator for async task queue functions."""
    if callable(name):
        fn = name
        return _create_decorator("task_queue")(fn)
    kwargs["name"] = name
    kwargs.setdefault("keep_warm", 10)
    return _create_decorator("task_queue", **kwargs)


def schedule(name: str | None = None, cron: str = "", **kwargs):
    """Decorator for cron-scheduled functions."""
    if callable(name):
        fn = name
        return _create_decorator("schedule")(fn)
    kwargs["name"] = name
    kwargs["cron"] = cron
    return _create_decorator("schedule", **kwargs)
