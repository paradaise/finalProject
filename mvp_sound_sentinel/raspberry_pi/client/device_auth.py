"""
Device authentication client for Raspberry Pi.
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Optional
import requests


class DeviceAuthClient:
    """Client for device authentication."""
    
    def __init__(self, api_server_url: str):
        self.api_server_url = api_server_url.rstrip('/')
        self.credentials = None
        self.session = requests.Session()
    
    def load_credentials(self, device_id: str, api_key: str, device_secret: str):
        """Load device credentials."""
        self.credentials = {
            "device_id": device_id,
            "api_key": api_key,
            "device_secret": device_secret
        }
    
    def request_credentials(self, device_id: str, admin_key: str) -> Dict[str, str]:
        """
        Request new credentials from server.
        
        Args:
            device_id: Device ID
            admin_key: Admin key for authorization
            
        Returns:
            Dictionary with device credentials
        """
        url = f"{self.api_server_url}/auth/device_credentials"
        
        payload = {
            "device_id": device_id
        }
        
        headers = {
            "X-Admin-Key": admin_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            credentials = response.json()
            self.load_credentials(
                credentials["device_id"],
                credentials["api_key"],
                credentials["device_secret"]
            )
            
            return credentials
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to request credentials: {e}")
    
    def generate_signature(self, payload: Dict[str, any]) -> str:
        """Generate HMAC signature for request."""
        if not self.credentials:
            raise Exception("No credentials loaded")
        
        timestamp = int(time.time())
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        
        message = f"{timestamp}:{payload_str}"
        signature = hmac.new(
            self.credentials["device_secret"].encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature, timestamp
    
    def make_authenticated_request(self, method: str, endpoint: str, 
                                 payload: Optional[Dict] = None,
                                 **kwargs) -> requests.Response:
        """
        Make authenticated request to API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            payload: Request payload
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        if not self.credentials:
            raise Exception("No credentials loaded")
        
        url = f"{self.api_server_url}{endpoint}"
        
        # Prepare payload
        if payload is None:
            payload = {}
        
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        
        # Generate signature
        signature, timestamp = self.generate_signature(payload)
        
        # Add auth headers
        headers = kwargs.pop('headers', {})
        headers.update({
            'X-Device-ID': self.credentials['device_id'],
            'X-Signature': signature,
            'X-Timestamp': str(timestamp),
            'Content-Type': 'application/json'
        })
        
        # Make request
        if method.upper() == 'GET':
            response = self.session.get(url, headers=headers, params=payload, **kwargs)
        elif method.upper() == 'POST':
            response = self.session.post(url, data=payload_str, headers=headers, **kwargs)
        elif method.upper() == 'PUT':
            response = self.session.put(url, data=payload_str, headers=headers, **kwargs)
        elif method.upper() == 'DELETE':
            response = self.session.delete(url, headers=headers, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    
    def check_auth_status(self) -> bool:
        """Check if authentication is working."""
        try:
            endpoint = f"/auth/device/{self.credentials['device_id']}/status"
            response = self.make_authenticated_request('GET', endpoint)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_auth_info(self) -> Dict[str, str]:
        """Get current authentication info."""
        if not self.credentials:
            return {"status": "no_credentials"}
        
        return {
            "device_id": self.credentials["device_id"],
            "api_key": self.credentials["api_key"][:8] + "...",  # Show only first 8 chars
            "status": "loaded"
        }


# Convenience function for quick setup
def setup_device_auth(api_server_url: str, device_id: str, 
                     credentials_file: str = "device_credentials.json") -> DeviceAuthClient:
    """
    Setup device authentication from file or request new credentials.
    
    Args:
        api_server_url: API server URL
        device_id: Device ID
        credentials_file: Path to credentials file
        
    Returns:
        Configured DeviceAuthClient
    """
    import os
    import json
    
    auth_client = DeviceAuthClient(api_server_url)
    
    # Try to load from file
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
            
            auth_client.load_credentials(
                credentials["device_id"],
                credentials["api_key"],
                credentials["device_secret"]
            )
            
            # Test credentials
            if auth_client.check_auth_status():
                print(f"   Loaded existing credentials for device {device_id}")
                return auth_client
            else:
                print(f"   Invalid credentials, requesting new ones...")
                
        except Exception as e:
            print(f"   Error loading credentials: {e}")
    
    # Request new credentials
    print(f"   Requesting new credentials for device {device_id}")
    print("   You'll need the admin key from the server setup")
    
    admin_key = input("   Enter admin key: ").strip()
    
    try:
        credentials = auth_client.request_credentials(device_id, admin_key)
        
        # Save to file
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"   Credentials saved to {credentials_file}")
        print(f"   Device ID: {credentials['device_id']}")
        print(f"   API Key: {credentials['api_key'][:8]}...")
        
        return auth_client
        
    except Exception as e:
        raise Exception(f"Failed to setup authentication: {e}")
