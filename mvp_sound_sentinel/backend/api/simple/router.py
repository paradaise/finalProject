from fastapi import APIRouter

from backend.api.simple.register_device import router as register_device_router
from backend.api.simple.detect_sound import router as detect_sound_router
from backend.api.simple.devices import router as devices_router
from backend.api.simple.health import router as health_router
from backend.api.simple.ws import router as ws_router


router = APIRouter()
router.include_router(register_device_router)
router.include_router(detect_sound_router)
router.include_router(devices_router)
router.include_router(health_router)
router.include_router(ws_router)

