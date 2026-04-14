"""
Device Authentication API
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import sqlite3
from backend.api.simple import state
from backend.auth.device_auth import device_auth


router = APIRouter()


class DeviceCredentialsRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = None


class DeviceCredentialsResponse(BaseModel):
    device_id: str
    api_key: str
    device_secret: str
    message: str


@router.post("/auth/device_credentials")
async def get_device_credentials(
    request: DeviceCredentialsRequest, x_admin_key: Optional[str] = Header(default=None)
):
    """
    Get API credentials for a device.

    This endpoint requires an admin key for security.
    """
    import os

    # Get admin key from environment
    ADMIN_KEY = os.getenv("ADMIN_KEY", "sound-sentinel-admin-2024")

    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    # Check if device exists
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM devices WHERE id = ?", (request.device_id,))

    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    conn.close()

    # Generate credentials
    credentials = device_auth.generate_device_credentials(request.device_id)

    return DeviceCredentialsResponse(
        device_id=credentials["device_id"],
        api_key=credentials["api_key"],
        device_secret=credentials["device_secret"],
        message="Credentials generated successfully",
    )


@router.get("/auth/device/{device_id}/status")
async def get_device_auth_status(device_id: str):
    """Get authentication status for a device."""
    credentials = device_auth.get_device_credentials(device_id)

    if not credentials:
        raise HTTPException(status_code=404, detail="Device credentials not found")

    return {"device_id": device_id, "has_credentials": True, "is_active": True}


@router.post("/auth/device/{device_id}/deactivate")
async def deactivate_device(device_id: str):
    """Deactivate a device's authentication."""
    success = device_auth.deactivate_device(device_id)

    if not success:
        raise HTTPException(
            status_code=404, detail="Device not found or already inactive"
        )

    return {"device_id": device_id, "message": "Device deactivated successfully"}


@router.get("/auth/devices")
async def list_authenticated_devices():
    """List all devices with authentication credentials."""
    conn = sqlite3.connect(state.db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dk.device_id, dk.api_key, dk.created_at, dk.last_used, dk.is_active,
               d.name as device_name, d.status as device_status
        FROM device_keys dk
        JOIN devices d ON dk.device_id = d.id
        ORDER BY dk.created_at DESC
    """
    )

    devices = []
    for row in cursor.fetchall():
        devices.append(
            {
                "device_id": row[0],
                "api_key": row[1][:8] + "...",  # Show only first 8 chars
                "created_at": row[2],
                "last_used": row[3],
                "is_active": bool(row[4]),
                "device_name": row[5],
                "device_status": row[6],
            }
        )

    conn.close()

    return {"devices": devices}
