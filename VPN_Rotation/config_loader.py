"""
config.py — Flat config loader.
Flattens the nested config.json into a single dict for easy access.
"""

import json
import os

def load_config(path: str = "config.json") -> dict:
    """Load and flatten config.json into a single dict."""
    config_path = path if os.path.isabs(path) else os.path.join(os.path.dirname(__file__), path)
    with open(config_path) as f:
        raw = json.load(f)

    flat = {}
    for section, values in raw.items():
        if section == "comment":
            continue
        if isinstance(values, dict):
            flat.update(values)
        else:
            flat[section] = values
    return flat
