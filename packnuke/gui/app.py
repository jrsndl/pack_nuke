"""GUI start-up: logging, style, resources, main window."""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys

from PySide6 import QtGui, QtWidgets


def app_dir() -> str:
    """Folder holding settings.ini: next to the exe when frozen, else the repository root."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable).replace('\\', '/')
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here)).replace('\\', '/')


def setup_logging(folder: str):
    from .tab_log import QtLogHandler
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for h in list(root.handlers):
        root.removeHandler(h)
    fmt = logging.Formatter('%(asctime)s %(levelname)-8s %(name)s: %(message)s')
    try:
        fh = logging.handlers.RotatingFileHandler(os.path.join(folder, 'pack_nuke_gui.log'), maxBytes=2_000_000,
                                                  backupCount=3, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    root.addHandler(sh)
    qt = QtLogHandler()
    root.addHandler(qt)

    def excepthook(exc_type, exc, tb):
        logging.getLogger('packnuke.gui').critical('Unhandled exception', exc_info=(exc_type, exc, tb))
    sys.excepthook = excepthook
    return qt


def main() -> int:
    folder = app_dir()
    if folder not in sys.path:
        sys.path.insert(0, folder)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Pack Nuke')
    app.setStyle('Fusion')
    try:
        import importlib
        importlib.import_module('ui_images_rc')  # registers the :/images/... resources
    except ImportError:
        pass
    font = QtGui.QFont(app.font())
    font.setPointSize(10)          # set in code, not in style.qss (see the note there)
    app.setFont(font)
    qss = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.qss')
    if os.path.isfile(qss):
        with open(qss, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    handler = setup_logging(folder)
    from .main_window import MainWindow
    win = MainWindow(folder, handler)
    win.show()
    return app.exec()
