# Wistfare Python SDK

The official Python SDK for the [Wistfare Serverless GPU Platform](https://wistfare.com).

## Installation

```bash
pip install wistfare
```

## Quick Start

```python
from wistfare import endpoint, Image

image = Image(
    python_version="3.12",
    python_packages=["torch", "transformers"],
    cuda_version="12.4",
)

@endpoint(name="predict", cpu=2, memory="16Gi", gpu="H100", image=image)
def predict(context, prompt: str = ""):
    model = context.on_start_result
    return model.generate(prompt)

@predict.on_start()
def load_model(context):
    from transformers import pipeline
    return pipeline("text-generation", model="meta-llama/Llama-3-8B", device="cuda")
```

```bash
wistfare deploy app.py:predict
```

## Features

- **Decorators**: `@endpoint`, `@function`, `@task_queue`, `@schedule`
- **GPU Support**: RTX 4090, A100, H100 with per-second billing
- **Image Builder**: Define container environments with `Image()`
- **CLI**: `wistfare deploy`, `wistfare serve`, `wistfare logs`
- **Client**: Programmatic invocation via `WistfareClient`

## Documentation

See the [Getting Started Guide](https://github.com/Wistfare/cloud/blob/main/docs/serverless-gpu/getting-started.md).

## License

MIT
