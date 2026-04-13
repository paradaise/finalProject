#!/usr/bin/env python3
"""
Sound Sentinel MVP - Raspberry Pi Client Runner
"""

import sys
import os

# Add client directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client'))

from audio_client_app import AudioClient

if __name__ == "__main__":
    client = AudioClient()
    try:
        client.start()
    except KeyboardInterrupt:
        print("\nStopping client...")
        client.stop()
