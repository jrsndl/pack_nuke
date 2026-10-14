"""Background threads: script scan and Deadline submission."""
from __future__ import annotations

import logging
import threading
from typing import List, Tuple

from PySide6 import QtCore

from ..core.scanner import NkScanner, ScanStats
from ..core.versions import ScriptEntry
from ..farm import deadline

log = logging.getLogger('packnuke.gui')


class ScanWorker(QtCore.QThread):
    """Runs :class:`NkScanner`; delivers found folders in batches (~5x per second)."""
    batch = QtCore.Signal(object)        # List[Tuple[folder, List[ScriptEntry]]]
    progress = QtCore.Signal(object)     # ScanStats
    done = QtCore.Signal(object)         # ScanStats

    def __init__(self, root: str, workers: int, skip_dirs: List[str], max_depth: int, parent=None):
        super().__init__(parent)
        self.scanner = NkScanner(root, workers=workers, skip_dirs=skip_dirs, max_depth=max_depth)
        self._lock = threading.Lock()
        self._pending: List[Tuple[str, List[ScriptEntry]]] = []

    def stop(self) -> None:
        self.scanner.stop()

    def _on_folder(self, folder: str, entries: List[ScriptEntry]) -> None:
        with self._lock:
            self._pending.append((folder, entries))

    def _flush(self) -> None:
        with self._lock:
            pending, self._pending = self._pending, []
        if pending:
            self.batch.emit(pending)

    def _on_progress(self, stats: ScanStats) -> None:
        self._flush()
        self.progress.emit(stats)

    def run(self) -> None:
        try:
            stats = self.scanner.run(self._on_folder, self._on_progress, progress_interval=0.2)
        except Exception as e:  # never kill the GUI
            log.exception('Scan failed: %s', e)
            stats = self.scanner.stats
        self._flush()
        self.done.emit(stats)


class SubmitWorker(QtCore.QThread):
    """Submits every script of a job to Deadline, one after another."""
    result = QtCore.Signal(object, int, int)   # SubmitResult, done, total
    done = QtCore.Signal(int, int)             # ok count, failed count

    def __init__(self, cfg, job, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.job = job
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        ok = failed = 0
        total = len(self.job.scripts)
        for i, script in enumerate(self.job.scripts):
            if self._stop:
                break
            res = deadline.submit_script(self.cfg, self.job, script)
            if res.ok:
                ok += 1
            else:
                failed += 1
            self.result.emit(res, i + 1, total)
        self.done.emit(ok, failed)
