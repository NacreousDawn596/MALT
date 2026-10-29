"""PyInstaller entry point for the MALT Qt6 notebook GUI (windowed app)."""
from malt.cli import gui_main

if __name__ == "__main__":
    raise SystemExit(gui_main())
