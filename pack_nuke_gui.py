"""Pack Nuke GUI entry point: ``python pack_nuke_gui.py`` (needs PySide6)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packnuke.gui.app import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
