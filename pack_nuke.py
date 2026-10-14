"""Farm entry point - run inside Nuke:

    nuke -t pack_nuke.py --job-dir <package>/_pack_nuke --id <script id>

The Deadline jobs submitted by the GUI call exactly this. All logic lives in the
``packnuke`` package next to this file.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packnuke.farm.pack_job import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
