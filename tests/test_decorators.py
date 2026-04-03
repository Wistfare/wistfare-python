"""Tests for function decorators."""

import pytest
from wistfare import endpoint, function, task_queue, schedule
from wistfare.image import Image


def test_endpoint_decorator():
    image = Image(python_packages=["torch"])

    @endpoint(name="predict", cpu=2, memory="16Gi", gpu="H100", image=image)
    def predict(context, **inputs):
        return {"result": "test"}

    assert hasattr(predict, "_wistfare_config")
    config = predict._wistfare_config
    assert config.name == "predict"
    assert config.invoke_type == "endpoint"
    assert config.cpu == 2
    assert config.memory == "16Gi"
    assert config.gpu == "H100"
    assert config.gpu_count == 1
    assert config.keep_warm == 180  # endpoint default
    assert config.image is image


def test_function_decorator():
    @function(name="embed", cpu=1, memory="4Gi", gpu="RTX_4090")
    def embed(context, texts):
        return []

    config = embed._wistfare_config
    assert config.name == "embed"
    assert config.invoke_type == "function"
    assert config.gpu == "RTX_4090"
    assert config.keep_warm == 60  # function default


def test_task_queue_decorator():
    @task_queue(name="train", gpu="A100_80GB", timeout=3600)
    def train(context, **inputs):
        pass

    config = train._wistfare_config
    assert config.name == "train"
    assert config.invoke_type == "task_queue"
    assert config.timeout == 3600
    assert config.keep_warm == 10  # task_queue default


def test_schedule_decorator():
    @schedule(name="cleanup", cron="0 * * * *")
    def cleanup(context):
        pass

    config = cleanup._wistfare_config
    assert config.name == "cleanup"
    assert config.invoke_type == "schedule"
    assert config.schedule_cron == "0 * * * *"


def test_decorator_without_name_uses_function_name():
    @function()
    def my_func(context):
        pass

    assert my_func._wistfare_config.name == "my_func"


def test_on_start_hook():
    @endpoint(name="predict", gpu="H100")
    def predict(context, **inputs):
        return context.on_start_result

    @predict.on_start()
    def load_model(context):
        return "loaded_model"

    config = predict._wistfare_config
    assert config.on_start_handler is not None
    assert config.on_start_handler.__name__ == "load_model"


def test_image_builder():
    image = Image(
        python_version="3.12",
        python_packages=["torch", "transformers"],
        system_packages=["libgl1"],
        cuda_version="12.4",
    )
    d = image.to_dict()
    assert d["python_version"] == "3.12"
    assert "torch" in d["python_packages"]
    assert d["cuda_version"] == "12.4"


def test_image_chaining():
    image = Image().add_python_packages(["torch"]).add_system_packages(["libgl1"])
    assert "torch" in image.python_packages
    assert "libgl1" in image.system_packages


def test_parse_memory():
    from wistfare.decorators import _parse_memory
    assert _parse_memory("512Mi") == 512
    assert _parse_memory("2Gi") == 2048
    assert _parse_memory("1G") == 1024
    assert _parse_memory("256M") == 256
    assert _parse_memory("1024") == 1024
