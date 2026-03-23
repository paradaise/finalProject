from __future__ import annotations

import socket
import uuid
from typing import Dict


def get_real_ip_address() -> str:
    """Get real LAN IP instead of 127.0.0.1."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"


def get_model_image_url(model_name: str) -> str:
    model_lower = model_name.lower()

    if "zero 2 w" in model_lower:
        return "/images/raspberry-pi-zero-2-w.png"
    if "zero w" in model_lower:
        return "/images/raspberry-pi-zero-w.png"
    if "zero" in model_lower:
        return "/images/raspberry-pi-zero.png"
    if "4" in model_lower:
        if "compute" in model_lower:
            return "/images/raspberry-pi-4-compute.png"
        return "/images/raspberry-pi-4.png"
    if "3" in model_lower:
        if "a+" in model_lower:
            return "/images/raspberry-pi-3-a-plus.png"
        if "b+" in model_lower:
            return "/images/raspberry-pi-3-b-plus.png"
        return "/images/raspberry-pi-3.png"
    if "2" in model_lower:
        return "/images/raspberry-pi-2.png"
    if "1" in model_lower:
        if "b+" in model_lower:
            return "/images/raspberry-pi-1-b-plus.png"
        return "/images/raspberry-pi-1.png"
    return "/images/raspberry-pi-default.png"


def get_raspberry_pi_model() -> Dict[str, str]:
    """Detect Raspberry Pi model and image URL."""
    try:
        model_name = None

        # Try device tree first
        try:
            with open("/sys/firmware/devicetree/base/model", "r") as f:
                model_info = f.read().strip()
                if "Raspberry Pi" in model_info:
                    model_name = model_info
        except:
            pass

        # Fallback to /proc/cpuinfo
        if not model_name:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("Model"):
                        model_info = line.split(":")[1].strip()
                        if "Raspberry Pi" in model_info:
                            model_name = model_info
                            break

        if not model_name:
            return {"name": "Raspberry Pi", "image_url": "/images/raspberry-pi-default.png"}

        return {"name": model_name, "image_url": get_model_image_url(model_name)}
    except:
        return {"name": "Raspberry Pi", "image_url": "/images/raspberry-pi-default.png"}


def get_microphone_info() -> str:
    """Get microphone description."""
    try:
        import subprocess

        # arecord
        try:
            result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "card" in line and "device" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            return parts[1].strip()
        except:
            pass

        # pactl
        try:
            result = subprocess.run(
                ["pactl", "list", "sources"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "Description:" in line:
                        return line.split("Description:")[1].strip()
        except:
            pass

        return "Default Microphone"
    except:
        return "Unknown Microphone"


def get_wifi_signal() -> int:
    """Get WiFi signal level (roughly) in percent."""
    try:
        import subprocess

        # Prefer nmcli
        result = subprocess.run(["nmcli", "dev", "wifi"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            for line in lines:
                if line.strip().startswith("*"):
                    parts = line.split()
                    if len(parts) > 7:
                        signal_percent = parts[7]
                        try:
                            return int(signal_percent)
                        except:
                            return 50
            return 50

        # Fallback to iwconfig
        try:
            result = subprocess.run(["iwconfig"], capture_output=True, text=True)
            if result.returncode == 0:
                import re

                lines = result.stdout.split("\n")
                for line in lines:
                    if "wlan" in line.lower() and "Signal level" in line:
                        match = re.search(r"Signal level=(-?\\d+) dBm", line)
                        if match:
                            dbm = int(match.group(1))
                            if dbm <= -100:
                                return 0
                            if dbm >= -50:
                                return 100
                            return 2 * (dbm + 100)
        except:
            pass

        return 50
    except:
        return 50


def collect_device_info(device_name: str) -> Dict[str, str]:
    """Collect full device info payload for /register_device."""
    try:
        ip_address = get_real_ip_address()

        mac = ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 2 * 6, 2)
            ][::-1]
        )

        model_info = get_raspberry_pi_model()
        microphone_info = get_microphone_info()
        wifi_signal = get_wifi_signal()

        return {
            "name": device_name,
            "ip_address": ip_address,
            "mac_address": mac,
            "model": model_info["name"],
            "model_image_url": model_info["image_url"],
            "microphone_info": microphone_info,
            "wifi_signal": wifi_signal,
        }
    except Exception as e:
        print(f"❌ Ошибка получения информации об устройстве: {e}")
        return None

