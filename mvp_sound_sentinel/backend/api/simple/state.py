from __future__ import annotations

from typing import Any, List, Set


# Shared server state for main_simple handlers.
# Lifespan in `backend/main_simple.py` initializes these fields.
db_path: str = "soundsentinel.db"
model: Any = None
class_names: List[str] = []
websocket_connections: Set[Any] = set()

