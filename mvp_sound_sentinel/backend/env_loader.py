from __future__ import annotations

import os
from typing import Optional


def load_env_file(env_path: Optional[str] = None) -> None:
    """Load simple KEY=VALUE pairs from a .env-like file.

    No extra dependencies; safe defaults:
    - ignore empty lines and comments (# ...)
    - ignore malformed lines
    - do not override already-set environment variables
    """
    if env_path is None:
        env_path = os.path.join(os.path.dirname(__file__), ".env")

    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Never crash server startup because of env parsing.
        return

