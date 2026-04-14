from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def suppress_alsa_errors() -> Iterator[None]:
    """Suppress ALSA stderr messages via stderr redirection."""
    original_stderr_fd = sys.stderr.fileno()
    saved_stderr_fd = os.dup(original_stderr_fd)
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, original_stderr_fd)
        yield
    finally:
        os.dup2(saved_stderr_fd, original_stderr_fd)
        os.close(saved_stderr_fd)
