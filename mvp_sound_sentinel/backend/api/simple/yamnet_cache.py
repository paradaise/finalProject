from fastapi import APIRouter
from typing import Dict, Any

from backend.utils.yamnet_cached import get_cache_info, clear_yamnet_cache


router = APIRouter()


@router.get("/yamnet/cache")
async def get_yamnet_cache_info() -> Dict[str, Any]:
    """Получение информации о кэше YAMNet"""
    try:
        cache_info = get_cache_info()
        return {
            "success": True,
            "cache_info": cache_info,
            "message": "Информация о кэше получена"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка получения информации о кэше"
        }


@router.delete("/yamnet/cache")
async def clear_yamnet_cache_endpoint() -> Dict[str, Any]:
    """Очистка кэша YAMNet (принудительное скачивание модели)"""
    try:
        success = clear_yamnet_cache()
        return {
            "success": success,
            "message": "Кэш YAMNet очищен" if success else "Ошибка очистки кэша"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка очистки кэша"
        }
