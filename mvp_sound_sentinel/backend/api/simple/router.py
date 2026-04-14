from fastapi import APIRouter

from backend.api.simple.register_device import router as register_device_router
from backend.api.simple.detect_sound import router as detect_sound_router
from backend.api.simple.update_device_info import router as update_device_info_router
from backend.api.simple.devices import router as devices_router
from backend.api.simple.custom_sounds_api import router as custom_sounds_router
from backend.api.simple.notification_settings import (
    router as notification_settings_router,
)
from backend.api.simple.yamnet_sounds import router as yamnet_sounds_router
from backend.api.simple.save_notification_settings import (
    router as save_notification_settings_router,
)
from backend.api.simple.clear_detections import router as clear_detections_router
from backend.api.simple.notification_settings import (
    router as notification_settings_router,
)
from backend.api.simple.custom_sounds_api import router as custom_sounds_router
from backend.api.simple.health import router as health_router
from backend.api.simple.ws import router as ws_router
from backend.api.simple.cleanup_devices import router as cleanup_router
from backend.api.simple.delete_device import router as delete_device_router
from backend.api.simple.save_notification_settings import (
    router as save_notification_settings_router,
)
from backend.api.simple.notification_sounds import router as notification_sounds_router
from backend.api.simple.excluded_sounds import router as excluded_sounds_router
from backend.api.simple.yamnet_cache import router as yamnet_cache_router


router = APIRouter()
router.include_router(register_device_router)
router.include_router(detect_sound_router)
router.include_router(update_device_info_router)
router.include_router(devices_router)
router.include_router(health_router)
router.include_router(ws_router)
router.include_router(cleanup_router)
router.include_router(delete_device_router)
router.include_router(clear_detections_router)
router.include_router(notification_settings_router)
router.include_router(custom_sounds_router)
router.include_router(yamnet_sounds_router)
router.include_router(save_notification_settings_router)
router.include_router(notification_sounds_router)
router.include_router(excluded_sounds_router)
router.include_router(yamnet_cache_router)
