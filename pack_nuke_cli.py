"""Pack Nuke command line: ``python pack_nuke_cli.py --help``.

Packs Nuke scripts without the GUI and prints the package root folder on stdout.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packnuke.cli import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
