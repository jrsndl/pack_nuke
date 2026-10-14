"""Log tab: every log record of the app, filterable by level, coloured, savable."""
from __future__ import annotations

import html
import logging
import time
from collections import deque
from typing import Deque, Tuple

from PySide6 import QtCore, QtGui, QtWidgets

from . import help as help_texts
from .widgets import button, hbox, label, vbox

LEVELS = [('Debug', logging.DEBUG), ('Info', logging.INFO), ('Warning', logging.WARNING),
          ('Error', logging.ERROR), ('Critical', logging.CRITICAL)]
COLORS = {logging.DEBUG: '#8a8a8a', logging.INFO: '#b1b1b1', logging.WARNING: '#ffa02f',
          logging.ERROR: '#ff6b5a', logging.CRITICAL: '#ff3b3b'}
MAX_RECORDS = 50000

Record = Tuple[float, int, str, str]  # time, level, logger, message


class QtLogBridge(QtCore.QObject):
    record = QtCore.Signal(float, int, str, str)


class QtLogHandler(logging.Handler):
    """Thread-safe: records from worker threads are queued to the GUI thread by the signal.
    Records logged before the Log tab exists are buffered and replayed on ``attach``."""

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.bridge = QtLogBridge()
        self._early: list = []
        self._attached = False

    def attach(self, slot) -> None:
        self.bridge.record.connect(slot)
        self._attached = True
        early, self._early = self._early, []
        for rec in early:
            slot(*rec)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            if record.exc_info:
                msg += '\n' + logging.Formatter().formatException(record.exc_info)
            if not self._attached:
                self._early.append((record.created, record.levelno, record.name, msg))
                return
            self.bridge.record.emit(record.created, record.levelno, record.name, msg)
        except Exception:
            self.handleError(record)


class LogTab(QtWidgets.QWidget):
    error_logged = QtCore.Signal(str)

    def __init__(self, handler: QtLogHandler, parent=None):
        super().__init__(parent)
        self.records: Deque[Record] = deque(maxlen=MAX_RECORDS)
        self.level_combo = QtWidgets.QComboBox()
        for name, lvl in LEVELS:
            self.level_combo.addItem(name, lvl)
        self.level_combo.setCurrentIndex(1)
        self.level_combo.currentIndexChanged.connect(self.rerender)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText('filter text')
        self.search.textChanged.connect(self.rerender)
        self.autoscroll = QtWidgets.QCheckBox('Auto scroll')
        self.autoscroll.setChecked(True)
        self.counts = label('')
        self.view = QtWidgets.QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setMaximumBlockCount(MAX_RECORDS)
        self.view.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.view.setFont(font)
        self._counts = {lvl: 0 for _n, lvl in LEVELS}
        help_texts.apply([(self.level_combo, 'Show level:'), (self.search, 'log_filter'),
                          (self.autoscroll, 'Auto scroll'), (self.view, 'Application messages; select text to copy it'), (self.counts, 'Warnings and errors logged so far')])

        self.setLayout(vbox(
            hbox(label('Show level:'), self.level_combo, label('  and above'), 12, self.search, self.autoscroll,
                 None, self.counts,
                 button('Clear', self.clear), button('Save...', self.save)),
            self.view, margins=6))
        handler.attach(self.add_record)

    def min_level(self) -> int:
        return int(self.level_combo.currentData())

    def _line(self, rec: Record) -> str:
        t, lvl, name, msg = rec
        stamp = time.strftime('%H:%M:%S', time.localtime(t))
        lvl_name = logging.getLevelName(lvl)
        text = html.escape('{} {:<8} {}'.format(stamp, lvl_name, msg)).replace('\n', '<br>')
        return '<span style="color:{}; white-space:pre">{}</span>'.format(COLORS.get(lvl, '#b1b1b1'), text)

    def _visible(self, rec: Record) -> bool:
        if rec[1] < self.min_level():
            return False
        needle = self.search.text().strip().lower()
        return not needle or needle in rec[3].lower()

    @QtCore.Slot(float, int, str, str)
    def add_record(self, t: float, lvl: int, name: str, msg: str) -> None:
        rec = (t, lvl, name, msg)
        self.records.append(rec)
        key = max([v for _n, v in LEVELS if v <= lvl] or [logging.DEBUG])
        self._counts[key] = self._counts.get(key, 0) + 1
        self._update_counts()
        if lvl >= logging.ERROR:
            self.error_logged.emit(msg)
        if self._visible(rec):
            self.view.appendHtml(self._line(rec))
            if self.autoscroll.isChecked():
                self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def _update_counts(self) -> None:
        w = self._counts.get(logging.WARNING, 0)
        e = self._counts.get(logging.ERROR, 0) + self._counts.get(logging.CRITICAL, 0)
        self.counts.setText('{} warnings, {} errors'.format(w, e))

    def rerender(self, *_args) -> None:
        self.view.setUpdatesEnabled(False)
        self.view.clear()
        lines = [self._line(r) for r in self.records if self._visible(r)]
        # appendHtml per block keeps one record per block (fast enough up to MAX_RECORDS)
        for line in lines:
            self.view.appendHtml(line)
        self.view.setUpdatesEnabled(True)
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def clear(self) -> None:
        self.records.clear()
        self._counts = {lvl: 0 for _n, lvl in LEVELS}
        help_texts.apply([(self.level_combo, 'Show level:'), (self.search, 'log_filter'),
                          (self.autoscroll, 'Auto scroll'), (self.view, 'Application messages; select text to copy it'), (self.counts, 'Warnings and errors logged so far')])
        self._update_counts()
        self.view.clear()

    def save(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save log', 'pack_nuke_log.txt', 'Text (*.txt)')
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            for t, lvl, name, msg in self.records:
                if self._visible((t, lvl, name, msg)):
                    f.write('{} {:<8} {}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)),
                                                   logging.getLevelName(lvl), msg))
