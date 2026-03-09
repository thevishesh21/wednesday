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


def brightness_up() -> str:
    """Increase screen brightness using PowerShell WMI."""
    try:
        subprocess.run(
            ["powershell", "-command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
             ".WmiSetBrightness(1, "
             "([Math]::Min(100, (Get-WmiObject -Namespace root/WMI "
             "-Class WmiMonitorBrightness).CurrentBrightness + 20)))"],
            capture_output=True, text=True, timeout=10,
        )
        return "Brightness increased."
    except Exception as e:
        return f"Could not change brightness: {e}"


def brightness_down() -> str:
    """Decrease screen brightness using PowerShell WMI."""
    try:
        subprocess.run(
            ["powershell", "-command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
             ".WmiSetBrightness(1, "
             "([Math]::Max(0, (Get-WmiObject -Namespace root/WMI "
             "-Class WmiMonitorBrightness).CurrentBrightness - 20)))"],
            capture_output=True, text=True, timeout=10,
        )
        return "Brightness decreased."
    except Exception as e:
        return f"Could not change brightness: {e}"


def open_task_manager() -> str:
    """Open Windows Task Manager."""
    try:
        subprocess.Popen(["taskmgr"], shell=True)
        return "Opening Task Manager."
    except Exception as e:
        return f"Failed to open Task Manager: {e}"


def empty_recycle_bin() -> str:
    """Empty the Windows Recycle Bin."""
    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)
        return "Recycle bin emptied."
    except Exception as e:
        return f"Failed to empty recycle bin: {e}"
