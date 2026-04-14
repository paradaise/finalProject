"""
Simple device authentication for Raspberry Pi clients.
"""

import hashlib
import hmac
import time
from typing import Optional, Dict, Any
import sqlite3
from backend.api.simple import state


class DeviceAuth:
    """Simple device authentication using API keys."""
    
    def __init__(self):
        self.db_path = state.db_path
        self._init_device_keys_table()
    
    def _init_device_keys_table(self):
        """Initialize device authentication keys table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_keys (
                device_id TEXT PRIMARY KEY,
                api_key TEXT UNIQUE NOT NULL,
                device_secret TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_device_credentials(self, device_id: str) -> Dict[str, str]:
        """Generate API key and secret for a device."""
        import secrets
        
        # Generate API key (32 characters)
        api_key = secrets.token_urlsafe(24)
        
        # Generate secret (64 characters)
        device_secret = secrets.token_urlsafe(48)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO device_keys 
            (device_id, api_key, device_secret, created_at, is_active)
            VALUES (?, ?, ?, datetime('now'), 1)
        """, (device_id, api_key, device_secret))
        
        conn.commit()
        conn.close()
        
        return {
            "device_id": device_id,
            "api_key": api_key,
            "device_secret": device_secret
        }
    
    def verify_device_request(self, device_id: str, signature: str, 
                            timestamp: int, payload: str) -> bool:
        """
        Verify device request signature.
        
        Args:
            device_id: Device ID
            signature: HMAC signature
            timestamp: Request timestamp
            payload: Request payload (JSON string)
            
        Returns:
            True if signature is valid
        """
        # Check timestamp (prevent replay attacks - 5 minute window)
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:  # 5 minutes
            return False
        
        # Get device secret
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT device_secret, is_active FROM device_keys 
            WHERE device_id = ?
        """, (device_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[1]:  # Not found or inactive
            return False
        
        device_secret = result[0]
        
        # Verify signature
        expected_signature = self._generate_signature(
            device_secret, timestamp, payload
        )
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    
    def _generate_signature(self, secret: str, timestamp: int, payload: str) -> str:
        """Generate HMAC signature for request."""
        message = f"{timestamp}:{payload}"
        return hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_device_credentials(self, device_id: str) -> Optional[Dict[str, str]]:
        """Get device credentials from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT api_key, device_secret, is_active 
            FROM device_keys 
            WHERE device_id = ?
        """, (device_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[2]:
            return None
        
        return {
            "device_id": device_id,
            "api_key": result[0],
            "device_secret": result[1]
        }
    
    def update_last_used(self, device_id: str):
        """Update last used timestamp for device."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE device_keys 
            SET last_used = datetime('now') 
            WHERE device_id = ?
        """, (device_id,))
        
        conn.commit()
        conn.close()
    
    def deactivate_device(self, device_id: str) -> bool:
        """Deactivate a device key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE device_keys 
            SET is_active = 0 
            WHERE device_id = ?
        """, (device_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success


# Global auth instance
device_auth = DeviceAuth()


def require_device_auth(func):
    """Decorator to require device authentication for API endpoints."""
    from functools import wraps
    from fastapi import HTTPException, Header
    from typing import Optional
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract auth headers
        device_id = kwargs.pop('x_device_id', None)
        signature = kwargs.pop('x_signature', None)
        timestamp = kwargs.pop('x_timestamp', None)
        
        if not all([device_id, signature, timestamp]):
            raise HTTPException(
                status_code=401,
                detail="Missing authentication headers"
            )
        
        try:
            timestamp_int = int(timestamp)
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="Invalid timestamp format"
            )
        
        # Get request body for signature verification
        request_body = kwargs.get('body', '{}')
        if hasattr(request_body, 'decode'):
            request_body = request_body.decode('utf-8')
        
        # Verify signature
        if not device_auth.verify_device_request(
            device_id, signature, timestamp_int, request_body
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid signature"
            )
        
        # Update last used
        device_auth.update_last_used(device_id)
        
        return await func(*args, **kwargs)
    
    return wrapper
