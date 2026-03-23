from typing import List, Optional

from pydantic import BaseModel


class DeviceRegistration(BaseModel):
    model_config = {"protected_namespaces": ()}
    name: str
    ip_address: str
    mac_address: str
    model: str
    model_image_url: Optional[str] = None
    microphone_info: Optional[str] = None
    wifi_signal: int = 0


class AudioData(BaseModel):
    device_id: str
    audio_data: List[float]
    sample_rate: int = 16000
    db_level: Optional[float] = None
    # main_simple historically accessed `audio_data.timestamp` even though
    # the schema didn't include it. Keep it optional for compatibility.
    timestamp: Optional[str] = None

