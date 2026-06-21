import os

try:
    # Load `.env` if present (optional).
    from raspberry_pi.env_loader import load_env_file

    load_env_file()
except Exception:
    pass


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


# Server
SERVER_HOST = os.getenv("SERVER_HOST", "172.20.10.5")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
USE_SSL = _env_bool("USE_SSL", True)

API_SERVER_URL = f"{'https' if USE_SSL else 'http'}://{SERVER_HOST}:{SERVER_PORT}"

# Device
DEVICE_NAME = os.getenv("DEVICE_NAME", "Raspberry Pi Monitor")

# Audio settings (keep defaults close to the working monolith)
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))  # YAMNet expects 16kHz
CHANNELS = int(os.getenv("CHANNELS", "1"))

# Intervals
# Prefer existing names from `raspberry_pi/.env.example`
LEVEL_UPDATE_INTERVAL = float(
    os.getenv("LEVEL_UPDATE_INTERVAL", os.getenv("AUDIO_LEVEL_UPDATE_INTERVAL", "1"))
)
DETECTION_INTERVAL = float(os.getenv("DETECTION_INTERVAL", "30"))

# How often to refresh device metadata.
# Default matches the previous monolith behaviour (once per detection batch).
DEVICE_INFO_UPDATE_INTERVAL = float(
    os.getenv("DEVICE_INFO_UPDATE_INTERVAL", str(DETECTION_INTERVAL))
)

# How often to refresh WiFi signal (can be same as device info interval).
WIFI_SIGNAL_UPDATE_INTERVAL = float(
    os.getenv("WIFI_SIGNAL_UPDATE_INTERVAL", "10")  # Changed to 10 seconds for testing
)

# Confidence threshold for printing/logging detections.
DETECTION_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "DETECTION_CONFIDENCE_THRESHOLD",
        os.getenv("DETECTION_THRESHOLD", "0.3"),
    )
)

# Derived values
CHUNK_DURATION = LEVEL_UPDATE_INTERVAL
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

DB_REFERENCE = float(os.getenv("DB_REFERENCE", "1.0"))
