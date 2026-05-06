"""Credential and connection config loader.

Priority (highest first):
  1. Environment variables
  2. ~/.protofiler/config.toml

The config file lives outside the repository so credentials are never
accidentally committed, even in a public repo.

Example ~/.protofiler/config.toml:

    [ib]
    host = "127.0.0.1"
    port = 7497
    client_id = 1

    [sinopac]
    api_key = "your_api_key"
    secret_key = "your_secret_key"
    ca_path = "/path/to/ca.pfx"
    ca_passwd = "your_ca_password"
    person_id = "A123456789"
"""

import os
import tomllib
from pathlib import Path
from typing import Any

_CONFIG_FILE = Path.home() / ".protofiler" / "config.toml"


def _load_toml() -> dict[str, Any]:
    if not _CONFIG_FILE.exists():
        return {}
    with _CONFIG_FILE.open("rb") as f:
        return tomllib.load(f)


def get(section: str, key: str, default: Any = None) -> Any:
    """Return a config value, preferring env vars over the config file."""
    env_key = f"{section.upper()}_{key.upper()}"
    if env_key in os.environ:
        return os.environ[env_key]
    toml = _load_toml()
    return toml.get(section, {}).get(key, default)


def section(name: str) -> dict[str, Any]:
    """Return all values for a section, with env vars taking precedence."""
    toml_section: dict[str, Any] = _load_toml().get(name, {})
    merged = dict(toml_section)
    prefix = f"{name.upper()}_"
    for env_key, value in os.environ.items():
        if env_key.startswith(prefix):
            field = env_key[len(prefix):].lower()
            merged[field] = value
    return merged
