#!/usr/bin/env python3
"""
Setup device authentication for Sound Sentinel.
"""

import sqlite3
import os
import json
from backend.auth.device_auth import device_auth


def setup_device_for_auth(device_id: str, device_name: str = None) -> dict:
    """
    Setup a device for authentication.
    
    Args:
        device_id: Device ID
        device_name: Optional device name
        
    Returns:
        Device credentials
    """
    # Check if device exists
    db_path = os.getenv("DB_PATH", "soundsentinel.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
    
    if not cursor.fetchone():
        conn.close()
        raise ValueError(f"Device {device_id} not found in database")
    
    conn.close()
    
    # Generate credentials
    credentials = device_auth.generate_device_credentials(device_id)
    
    print(f"   Device ID: {credentials['device_id']}")
    print(f"   API Key: {credentials['api_key']}")
    print(f"   Device Secret: {credentials['device_secret']}")
    print(f"   Device Name: {device_name or 'Not specified'}")
    
    return credentials


def list_authenticated_devices():
    """List all devices with authentication."""
    db_path = os.getenv("DB_PATH", "soundsentinel.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT dk.device_id, dk.api_key, dk.created_at, dk.last_used, dk.is_active,
               d.name as device_name, d.status as device_status
        FROM device_keys dk
        JOIN devices d ON dk.device_id = d.id
        ORDER BY dk.created_at DESC
    """)
    
    devices = cursor.fetchall()
    conn.close()
    
    if not devices:
        print("   No devices with authentication found")
        return
    
    print(f"   Found {len(devices)} device(s) with authentication:")
    print()
    
    for device in devices:
        status = "Active" if device[4] else "Inactive"
        last_used = device[3] or "Never"
        
        print(f"   Device: {device[0]}")
        print(f"   Name: {device[5]}")
        print(f"   Status: {device[6]} / Auth: {status}")
        print(f"   API Key: {device[1][:8]}...")
        print(f"   Created: {device[2]}")
        print(f"   Last Used: {last_used}")
        print()


def revoke_device_auth(device_id: str) -> bool:
    """Revoke authentication for a device."""
    success = device_auth.deactivate_device(device_id)
    
    if success:
        print(f"   Authentication revoked for device {device_id}")
    else:
        print(f"   Failed to revoke authentication for device {device_id}")
    
    return success


def main():
    """Main setup function."""
    print("Sound Sentinel - Device Authentication Setup")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Setup device for authentication")
        print("2. List authenticated devices")
        print("3. Revoke device authentication")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            device_id = input("Enter device ID: ").strip()
            device_name = input("Enter device name (optional): ").strip() or None
            
            try:
                setup_device_for_auth(device_id, device_name)
                
                # Save to file for easy transfer
                credentials = device_auth.get_device_credentials(device_id)
                filename = f"device_credentials_{device_id.replace(':', '_')}.json"
                
                with open(filename, 'w') as f:
                    json.dump(credentials, f, indent=2)
                
                print(f"   Credentials saved to {filename}")
                
            except Exception as e:
                print(f"   Error: {e}")
        
        elif choice == "2":
            list_authenticated_devices()
        
        elif choice == "3":
            device_id = input("Enter device ID to revoke: ").strip()
            revoke_device_auth(device_id)
        
        elif choice == "4":
            print("   Goodbye!")
            break
        
        else:
            print("   Invalid option. Please try again.")


if __name__ == "__main__":
    main()
