"""Pack Nuke - collect and relink everything a Nuke script needs.

Package layout:
    packnuke.core      pure Python logic (no Nuke, no Qt) - unit tested
    packnuke.nuke_io   the only code that talks to the ``nuke`` module
    packnuke.farm      farm entry point and Deadline submission
    packnuke.gui       PySide6 user interface
"""

__version__ = "2.0.0"
