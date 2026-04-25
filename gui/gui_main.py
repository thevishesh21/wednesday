"""
Wednesday AI Assistant — GUI Entry Point (standalone)
Can also be launched via:  python main.py  (default GUI mode)

Usage:
    python -m gui.gui_main
    python gui/gui_main.py
"""

import sys
import os

# Ensure project root is on sys.path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


def main():
    # Re-use main_gui() from main.py (single source of truth)
    from main import main_gui
    main_gui()


if __name__ == "__main__":
    main()
