"""
Wednesday - System Control Skill
Controls Windows system (shutdown, restart, sleep, lock, volume).
"""

import os
import subprocess


def shutdown() -> str:
    try:
        subprocess.Popen(["shutdown", "/s", "/t", "5"], shell=True)
        return "Shutting down the computer in 5 seconds."
    except Exception as e:
        return f"Failed to shut down: {e}"


def restart() -> str:
    try:
        subprocess.Popen(["shutdown", "/r", "/t", "5"], shell=True)
        return "Restarting the computer in 5 seconds."
    except Exception as e:
        return f"Failed to restart: {e}"


def sleep() -> str:
    try:
        subprocess.Popen(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
            shell=True,
        )
        return "Putting the computer to sleep."
    except Exception as e:
        return f"Failed to sleep: {e}"


def lock() -> str:
    try:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"], shell=True)
        return "Locking the computer."
    except Exception as e:
        return f"Failed to lock: {e}"


def volume_up() -> str:
    try:
        from ctypes import cast, POINTER
        import comtypes
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        new_vol = min(1.0, current + 0.1)
        volume.SetMasterVolumeLevelScalar(new_vol, None)
        return f"Volume increased to {int(new_vol * 100)}%."
    except ImportError:
        # Fallback if pycaw not installed
        try:
            import ctypes
            VK_VOLUME_UP = 0xAF
            KEYEVENTF_KEYUP = 0x2
            for _ in range(5):
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_KEYUP, 0)
            return "Volume increased."
        except Exception as e:
            return f"Failed to change volume: {e}"
    except Exception as e:
        return f"Failed to change volume: {e}"


def volume_down() -> str:
    try:
        import ctypes
        VK_VOLUME_DOWN = 0xAE
        KEYEVENTF_KEYUP = 0x2
        for _ in range(5):
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, KEYEVENTF_KEYUP, 0)
        return "Volume decreased."
    except Exception as e:
        return f"Failed to change volume: {e}"


def mute() -> str:
    try:
        import ctypes
        VK_VOLUME_MUTE = 0xAD
        KEYEVENTF_KEYUP = 0x2
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_KEYUP, 0)
        return "Toggled mute."
    except Exception as e:
        return f"Failed to mute: {e}"
