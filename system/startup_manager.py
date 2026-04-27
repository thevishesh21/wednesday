"""
WEDNESDAY AI OS — Startup Manager
Registers the assistant to run automatically on Windows boot.
"""

import os
import sys
import winreg

from core.logger import get_logger

log = get_logger("system.startup_manager")

class StartupManager:
    """Manages Windows Registry run keys."""
    
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "WednesdayAI"
    
    def __init__(self):
        # Determine the launch command. If running from python, we use python.exe main.py
        # If compiled to an exe, we use the exe path.
        if getattr(sys, 'frozen', False):
            self.exec_path = f'"{sys.executable}"'
        else:
            main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
            self.exec_path = f'"{sys.executable}" "{main_script}"'
            
    def is_registered(self) -> bool:
        """Check if Wednesday is set to run on startup."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, self.APP_NAME)
                return value == self.exec_path
        except FileNotFoundError:
            return False
        except Exception as e:
            log.error(f"Error checking startup registry: {e}")
            return False
            
    def enable(self) -> bool:
        """Add Wednesday to Windows startup."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, self.exec_path)
            log.info("Registered to run on Windows startup.")
            return True
        except Exception as e:
            log.error(f"Failed to enable startup: {e}")
            return False
            
    def disable(self) -> bool:
        """Remove Wednesday from Windows startup."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.APP_NAME)
            log.info("Removed from Windows startup.")
            return True
        except FileNotFoundError:
            # Already removed
            return True
        except Exception as e:
            log.error(f"Failed to disable startup: {e}")
            return False

startup_manager = StartupManager()
