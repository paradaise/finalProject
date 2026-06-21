from __future__ import annotations

import socket
import uuid
import psutil
import subprocess
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
            return {
                "name": "Raspberry Pi",
                "image_url": "/images/raspberry-pi-default.png",
            }

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

        # Use nmcli to get signal for active connection only
        result = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SIGNAL", "dev", "wifi", "list"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            for line in lines:
                # Format: "yes:80" for active connection
                if line.startswith("yes:"):
                    try:
                        signal = int(line.split(":")[1])
                        signal = max(0, min(100, signal))
                        print(f"  [WiFi] nmcli signal: {signal}%")
                        return signal
                    except:
                        pass

        # Fallback to full nmcli output
        result = subprocess.run(
            ["nmcli", "dev", "wifi"], capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            for line in lines:
                if line.strip().startswith("*"):
                    # Extract signal using regex - look for percentage pattern
                    import re
                    # Match pattern like "71" or "71%" in the line
                    match = re.search(r'\b(\d{1,3})%\b', line)
                    if match:
                        signal = int(match.group(1))
                        # Clamp to 0-100
                        signal = max(0, min(100, signal))
                        print(f"  [WiFi] nmcli signal: {signal}%")
                        return signal
            print(f"  [WiFi] nmcli no active connection found")

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
                            signal = 2 * (dbm + 100)
                            print(f"  [WiFi] iwconfig signal: {signal}% (dBm: {dbm})")
                            return signal
            print(f"  [WiFi] iwconfig no signal found")
        except Exception as e:
            print(f"  [WiFi] iwconfig error: {e}")

        print(f"  [WiFi] fallback to 50%")
        return 50
    except Exception as e:
        print(f"  [WiFi] error: {e}")
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
        cpu_usage = get_cpu_usage()
        device_temperature = get_device_temperature()

        return {
            "name": device_name,
            "ip_address": ip_address,
            "mac_address": mac,
            "model": model_info["name"],
            "model_image_url": model_info["image_url"],
            "microphone_info": microphone_info,
            "wifi_signal": wifi_signal,
            "cpu_usage": cpu_usage,
            "device_temperature": device_temperature,
        }
    except Exception as e:
        print(f"❌ Ошибка получения информации об устройстве: {e}")
        return None


def get_cpu_usage() -> float:
    """Get current CPU usage percentage."""
    try:
        return psutil.cpu_percent(interval=1)
    except:
        return 0.0


def get_device_temperature() -> float:
    """Get device temperature in Celsius."""
    try:
        # Try to get temperature from vcgencmd (Raspberry Pi specific)
        result = subprocess.run(
            ["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Output format: "temp=45.5'C"
            temp_str = result.stdout.strip()
            if "temp=" in temp_str:
                temp_value = temp_str.split("=")[1].replace("'C", "")
                return float(temp_value)
    except:
        pass

    try:
        # Fallback to psutil temperature sensors
        temps = psutil.sensors_temperatures()
        if temps:
            # Try common sensor names
            for sensor_name in ["cpu_thermal", "coretemp", "acpitz"]:
                if sensor_name in temps:
                    return temps[sensor_name][0].current
    except:
        pass

    return 0.0
