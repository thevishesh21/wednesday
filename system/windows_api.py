"""
WEDNESDAY AI OS — Windows API Wrappers
Low-level interactions with the Windows OS.
"""

import ctypes
import os
import sys

from core.logger import get_logger

log = get_logger("system.windows_api")

def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        log.error(f"Failed to check admin status: {e}")
        return False

def request_admin() -> bool:
    """
    Restart the script with admin privileges.
    Returns True if successful, False if the user denies the UAC prompt.
    """
    if is_admin():
        return True

    log.info("Requesting administrator privileges...")
    
    # sys.executable is python.exe, sys.argv[0] is the script path
    script = os.path.abspath(sys.argv[0])
    args = " ".join(sys.argv[1:])
    
    try:
        # 1 means SW_SHOWNORMAL
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {args}', None, 1)
        if ret <= 32:
            log.warning(f"UAC prompt denied or failed (Code {ret})")
            return False
            
        # The new elevated process has started. We should exit this one.
        sys.exit(0)
    except Exception as e:
        log.error(f"Failed to request admin: {e}")
        return False
