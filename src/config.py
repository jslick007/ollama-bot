import json
import os
from typing import Any, Dict, Optional
import yaml


DEFAULT_CONFIG = {
    "llm": {
        "provider": "openai",
        "model": "tinyllama:latest",
        "api_key": "ollama",
        "base_url": "http://192.168.1.75:11434/v1",
    },
    "planner": {
        "max_iterations": 10,
        "max_tool_errors": 3,
    },
    "memory": {
        "type": "in_memory",
        "ttl": 3600,
    },
    "prompt": {
        "max_tokens": 4096,
    },
    "self_reflection": {
        "enabled": False,
    },
    "telemetry": {
        "log_to_stdout": False,
        "log_file": None,
    },
    "server": {
        "port": 80,
    },
}


def _load_json(path: str) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _find_config(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if path:
        if os.path.isfile(path):
            loader = _load_json if path.endswith(".json") else _load_yaml
            return loader(path)
        return None
    for candidate in ["config.json", "config.yaml", "config.yml"]:
        if os.path.isfile(candidate):
            loader = _load_json if candidate.endswith(".json") else _load_yaml
            return loader(candidate)
    return None


def load_config(
    path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    # Always load external config file if present.
    file_config = _find_config(path)
    external_model = None
    if file_config:
        _deep_merge(config, file_config)
        external_model = config.get("llm", {}).get("model")
    # Apply any overrides, but preserve the external model if it was set.
    if overrides:
        _deep_merge(config, overrides)
        if external_model:
            # Force the model to stay as defined in external config.
            config.setdefault("llm", {})["model"] = external_model
    return config


def _deep_merge(base: Dict, override: Dict) -> Dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
