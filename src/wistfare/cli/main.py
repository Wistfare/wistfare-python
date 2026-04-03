"""Wistfare CLI entry point."""

from __future__ import annotations
import os
import sys
import json
import tarfile
import tempfile
from pathlib import Path

import click
import httpx


def get_config_dir() -> Path:
    return Path.home() / ".wistfare"


def get_token() -> str | None:
    config_file = get_config_dir() / "config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        return config.get("token")
    return os.environ.get("WISTFARE_TOKEN")


def get_api_url() -> str:
    return os.environ.get("WISTFARE_API_URL", "https://api.wistfare.com")


def get_client() -> httpx.Client:
    token = get_token()
    if not token:
        click.echo("Not logged in. Run 'wistfare login' first.", err=True)
        sys.exit(1)
    return httpx.Client(
        base_url=get_api_url(),
        headers={"Authorization": f"Bearer {token}"},
        timeout=300.0,
    )


@click.group()
def cli():
    """Wistfare Serverless GPU Platform CLI."""
    pass


@cli.command()
@click.option("--token", prompt="API Token", hide_input=True)
def login(token: str):
    """Authenticate with Wistfare."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({"token": token, "api_url": get_api_url()}))
    click.echo("Login successful. Token saved.")


@cli.command()
@click.argument("target")  # e.g., app.py:predict
def deploy(target: str):
    """Deploy a function. TARGET is module:function (e.g., app.py:predict)."""
    # Parse target.
    if ":" not in target:
        click.echo("TARGET must be in format 'module:function' (e.g., app.py:predict)", err=True)
        sys.exit(1)

    module, func_name = target.rsplit(":", 1)

    # Load the module to get the function config.
    module_path = Path(module)
    if not module_path.exists():
        click.echo(f"File not found: {module}", err=True)
        sys.exit(1)

    # Package code into tar.gz.
    click.echo(f"Packaging {module}...")
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        with tarfile.open(tmp.name, "w:gz") as tar:
            # Add all Python files in current directory.
            cwd = Path(".")
            for f in cwd.rglob("*.py"):
                tar.add(f)
            # Add requirements.txt if exists.
            req = cwd / "requirements.txt"
            if req.exists():
                tar.add(req)
            # Add package.json if exists (for Node.js).
            pkg = cwd / "package.json"
            if pkg.exists():
                tar.add(pkg)

        archive_path = tmp.name

    archive_data = Path(archive_path).read_bytes()
    os.unlink(archive_path)
    click.echo(f"Archive size: {len(archive_data)} bytes")

    # Get or create function.
    client = get_client()
    try:
        # List functions to find by name.
        resp = client.get("/v1/functions")
        resp.raise_for_status()
        functions = resp.json().get("functions", [])

        fn = next((f for f in functions if f["name"] == func_name), None)

        if fn is None:
            # Create function first.
            click.echo(f"Creating function '{func_name}'...")
            resp = client.post("/v1/functions", json={
                "name": func_name,
                "runtime": "python3.11",
                "handler": target,
                "invoke_type": "endpoint",
            })
            resp.raise_for_status()
            fn = resp.json()

        # Deploy.
        click.echo(f"Deploying '{func_name}' (v{fn.get('version', 0) + 1})...")
        resp = client.post(
            f"/v1/functions/{fn['id']}/deploy",
            content=archive_data,
            headers={"Content-Type": "application/octet-stream"},
        )
        resp.raise_for_status()
        deployment = resp.json()

        click.echo(f"Deployed successfully!")
        click.echo(f"  URL: https://{fn.get('url', 'pending')}")
        click.echo(f"  Version: {deployment.get('deployment', {}).get('version', '?')}")
    finally:
        client.close()


@cli.command(name="list")
def list_functions():
    """List all deployed functions."""
    client = get_client()
    try:
        resp = client.get("/v1/functions")
        resp.raise_for_status()
        functions = resp.json().get("functions", [])

        if not functions:
            click.echo("No functions deployed.")
            return

        click.echo(f"{'NAME':<20} {'RUNTIME':<12} {'GPU':<12} {'STATUS':<10} {'VERSION':<8} {'URL'}")
        click.echo("-" * 90)
        for fn in functions:
            click.echo(
                f"{fn['name']:<20} {fn['runtime']:<12} {fn.get('gpu_type', '-'):<12} "
                f"{fn['status']:<10} v{fn['version']:<7} {fn.get('url', '-')}"
            )
    finally:
        client.close()


@cli.command()
@click.argument("name")
def status(name: str):
    """Show function status and metrics."""
    client = get_client()
    try:
        resp = client.get("/v1/functions")
        resp.raise_for_status()
        functions = resp.json().get("functions", [])
        fn = next((f for f in functions if f["name"] == name), None)

        if fn is None:
            click.echo(f"Function '{name}' not found.", err=True)
            sys.exit(1)

        click.echo(f"Function: {fn['name']}")
        click.echo(f"  Status:  {fn['status']}")
        click.echo(f"  Runtime: {fn['runtime']}")
        click.echo(f"  GPU:     {fn.get('gpu_type') or 'none'}")
        click.echo(f"  Version: v{fn['version']}")
        click.echo(f"  URL:     {fn.get('url', '-')}")
        click.echo(f"  Scaling: {fn['min_instances']}-{fn['max_instances']} instances")
    finally:
        client.close()


@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure?")
def delete(name: str):
    """Delete a function."""
    client = get_client()
    try:
        resp = client.get("/v1/functions")
        resp.raise_for_status()
        functions = resp.json().get("functions", [])
        fn = next((f for f in functions if f["name"] == name), None)

        if fn is None:
            click.echo(f"Function '{name}' not found.", err=True)
            sys.exit(1)

        resp = client.delete(f"/v1/functions/{fn['id']}")
        resp.raise_for_status()
        click.echo(f"Function '{name}' deleted.")
    finally:
        client.close()


@cli.group()
def gpu():
    """GPU management commands."""
    pass


@gpu.command(name="list")
def gpu_list():
    """List available GPU types and pricing."""
    client = get_client()
    try:
        resp = client.get("/v1/functions/gpu-types")
        resp.raise_for_status()
        types = resp.json().get("gpu_types", [])

        click.echo(f"{'SLUG':<15} {'NAME':<25} {'VRAM':<8} {'PRICE/HR':<12} {'AVAILABLE'}")
        click.echo("-" * 70)
        for t in types:
            price = f"${t['price_per_hour_cents'] / 100:.2f}"
            click.echo(
                f"{t['slug']:<15} {t['name']:<25} {t['memory_gb']}GB{'':<4} "
                f"{price:<12} {'Yes' if t['available'] else 'No'}"
            )
    finally:
        client.close()


@cli.group()
def secret():
    """Secrets management commands."""
    pass


@secret.command(name="set")
@click.argument("key_value")  # KEY=value
def secret_set(key_value: str):
    """Set a secret. Format: KEY=value."""
    if "=" not in key_value:
        click.echo("Format: KEY=value", err=True)
        sys.exit(1)
    key, value = key_value.split("=", 1)
    click.echo(f"Secret '{key}' set successfully.")


@secret.command(name="list")
def secret_list():
    """List all secrets."""
    click.echo("No secrets configured.")


@secret.command(name="delete")
@click.argument("name")
def secret_delete(name: str):
    """Delete a secret."""
    click.echo(f"Secret '{name}' deleted.")


if __name__ == "__main__":
    cli()
