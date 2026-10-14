"""Get Nuke Scripts tab: scan once for every *.nk, then filter interactively."""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.scanner import ScanStats, parse_skip_patterns
from ..core.versions import ScriptEntry, VersionFilter
from .script_models import ScriptTableModel, SortProxy
from . import help as help_texts
from .widgets import (Debouncer, PathEdit, button, configure_table, first_selected_row, hbox, hint, label,
                      reveal, selected_rows, vbox)
from .workers import ScanWorker

log = logging.getLogger('packnuke.gui')


class ScriptsTab(QtWidgets.QWidget):
    status = QtCore.Signal(str)                 # status bar text
    busy = QtCore.Signal(bool)                  # scan running
    send_to_queue = QtCore.Signal(object)       # List[ScriptEntry]
    selection_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folders: Dict[str, List[ScriptEntry]] = {}   # every .nk found, per folder (unfiltered)
        self.worker: Optional[ScanWorker] = None
        self.last_stats: Optional[ScanStats] = None
        self.filter = VersionFilter()
        self._build()
        self._refilter_later = Debouncer(self.refilter, 150, self)
        for w in (self.search_for, self.search_contains, self.version_regex):
            w.textChanged.connect(self._refilter_later.trigger)
        for w in (self.first_enabled, self.last_enabled):
            w.toggled.connect(self._refilter_later.trigger)
        for w in (self.first_n, self.last_n):
            w.valueChanged.connect(self._refilter_later.trigger)

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        self.root = PathEdit('dir', placeholder='folder to search, e.g. //server/prj/shots')
        self.root.edit.returnPressed.connect(self.start_scan)
        self.search_btn = button('Search', self.start_scan, 'Find every *.nk under the root (Enter)',
                                 icon=':/images/system-search.png', object_name='primary')
        self.stop_btn = button('Stop', self.stop_scan, 'Stop the running search')
        self.stop_btn.setEnabled(False)
        self.skip_dirs = QtWidgets.QLineEdit()
        self.skip_dirs.setPlaceholderText('.*;render;renders;plates;_old')
        self.skip_dirs.setToolTip('Folder names (wildcards, separated by ;) that are never entered. '
                                  'Skipping big render/plate folders is the best way to speed up the search.')
        self.max_depth = QtWidgets.QSpinBox()
        self.max_depth.setRange(0, 64)
        self.max_depth.setSpecialValueText('unlimited')
        self.max_depth.setToolTip('How many folder levels below the root to search (0 = unlimited)')
        self.threads = QtWidgets.QSpinBox()
        self.threads.setRange(0, 64)
        self.threads.setSpecialValueText('auto')
        self.threads.setValue(0)
        self.threads.setToolTip('Folders listed in parallel. auto = 1 on local disks, 16 on network shares.\n'
                                'Network shares benefit from 16-32.')

        self.search_for = QtWidgets.QLineEdit('*.nk')
        self.search_for.setToolTip('File name patterns, separated by ; (e.g. *_comp_v???.nk)')
        self.search_contains = QtWidgets.QLineEdit()
        self.search_contains.setToolTip('Keep only paths containing this text (several alternatives: a;b)')
        self.version_regex = QtWidgets.QLineEdit()
        self.version_regex.setToolTip('Regex on the file name, group 1 = version, e.g. .*_v(\\d{3})\\.nk. '
                                      'Empty = no version parsing.')
        self.regex_state = label('')
        self.first_enabled = QtWidgets.QCheckBox('First versions:')
        self.first_n = QtWidgets.QSpinBox()
        self.first_n.setRange(1, 9999)
        self.last_enabled = QtWidgets.QCheckBox('Last versions:')
        self.last_enabled.setChecked(True)
        self.last_n = QtWidgets.QSpinBox()
        self.last_n.setRange(1, 9999)

        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.addWidget(label('Search for:'), 0, 0)
        grid.addWidget(self.search_for, 0, 1)
        grid.addWidget(label('Only if contains:'), 0, 2)
        grid.addWidget(self.search_contains, 0, 3)
        grid.addWidget(label('Version regex:'), 1, 0)
        grid.addLayout(hbox(self.version_regex, self.regex_state), 1, 1)
        grid.addLayout(hbox(self.first_enabled, self.first_n, 16, self.last_enabled, self.last_n, None), 1, 2, 1, 2)
        filters_box = QtWidgets.QGroupBox('Filters (instant, no new search)')
        filters_box.setLayout(grid)

        self.model = ScriptTableModel(self)
        self.proxy = SortProxy(self)
        self.proxy.setSourceModel(self.model)
        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxy)
        configure_table(self.table, stretch_col=3)
        self.table.setColumnWidth(0, 28)
        self.table.setColumnWidth(1, 320)
        self.table.setColumnWidth(2, 70)
        self.table.sortByColumn(1, QtCore.Qt.AscendingOrder)
        self.table.doubleClicked.connect(self._double_clicked)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.selectionModel().selectionChanged.connect(lambda *_: self.selection_changed.emit())
        self.model.marks_changed.connect(self._update_counts)
        self.model.modelReset.connect(lambda: self.selection_changed.emit())
        space = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), self.table)
        space.setContext(QtCore.Qt.WidgetShortcut)
        space.activated.connect(lambda: self.mark_selected(None))

        self.counts = label('')
        self.send_btn = button('Send marked to Queue  →', self.send_marked,
                               'Add the marked scripts to the Queue tab', object_name='primary')
        actions = hbox(
            button('Mark all', lambda: self.model.set_marks(None, True)),
            button('Mark none', lambda: self.model.set_marks(None, False)),
            8,
            button('Mark selected', lambda: self.mark_selected(True), 'Mark the highlighted rows'),
            button('Unmark selected', lambda: self.mark_selected(False), 'Unmark the highlighted rows'),
            button('Toggle selected', lambda: self.mark_selected(None), 'Space'),
            None, self.counts, 12, self.send_btn)

        top = QtWidgets.QGridLayout()
        top.setColumnStretch(1, 1)
        top.addWidget(label('Search root:'), 0, 0)
        top.addLayout(hbox(self.root, self.search_btn, self.stop_btn), 0, 1)
        top.addWidget(label('Skip folders:'), 1, 0)
        top.addLayout(hbox(self.skip_dirs, label('Max depth:'), self.max_depth, label('Parallel:'), self.threads), 1, 1)

        help_texts.apply([
            (self.root, 'Search root:'), (self.root.edit, 'Search root:'), (self.skip_dirs, 'Skip folders:'),
            (self.max_depth, 'Max depth:'), (self.threads, 'Parallel:'), (self.search_for, 'Search for:'),
            (self.search_contains, 'Only if contains:'), (self.version_regex, 'Version regex:'),
            (self.first_enabled, 'First versions:'), (self.first_n, 'First versions:'),
            (self.last_enabled, 'Last versions:'), (self.last_n, 'Last versions:'),
            (self.table, 'scripts_table'), (self.counts, 'Shown rows / marked rows')])
        self.setLayout(vbox(top, hint('The search collects every *.nk once; the filters below then work '
                                      'on that list instantly.'), filters_box, self.table, actions, margins=6))

    # ------------------------------------------------------------------ state for presets / ini
    def get_state(self) -> dict:
        return {
            'search_root': self.root.text(),
            'skip_dirs': self.skip_dirs.text(),
            'max_depth': self.max_depth.value(),
            'scan_threads': self.threads.value(),
            'search_for': self.search_for.text(),
            'search_contains': self.search_contains.text(),
            'search_version_regex': self.version_regex.text(),
            'versions_get_first': self.first_enabled.isChecked(),
            'versions_first': self.first_n.value(),
            'versions_get_last': self.last_enabled.isChecked(),
            'versions_last': self.last_n.value(),
        }

    def set_state(self, s: dict) -> None:
        from .state import to_bool, to_int
        if 'search_root' in s:
            self.root.setText(str(s['search_root'] or ''))
        if 'skip_dirs' in s:
            self.skip_dirs.setText(str(s['skip_dirs'] or ''))
        if 'max_depth' in s:
            self.max_depth.setValue(to_int(s['max_depth'], 0))
        if 'scan_threads' in s:
            self.threads.setValue(to_int(s['scan_threads'], 0))
        if 'search_for' in s:
            self.search_for.setText(str(s['search_for'] or '*.nk'))
        if 'search_contains' in s:
            self.search_contains.setText(str(s['search_contains'] or ''))
        if 'search_version_regex' in s:
            self.version_regex.setText(str(s['search_version_regex'] or ''))
        if 'versions_get_first' in s:
            self.first_enabled.setChecked(to_bool(s['versions_get_first']))
        if 'versions_first' in s:
            self.first_n.setValue(to_int(s['versions_first'], 1))
        if 'versions_get_last' in s:
            self.last_enabled.setChecked(to_bool(s['versions_get_last'], True))
        if 'versions_last' in s:
            self.last_n.setValue(to_int(s['versions_last'], 1))
        self.refilter()

    # ------------------------------------------------------------------ scanning
    def start_scan(self) -> None:
        root = self.root.text()
        if not root or not os.path.isdir(root):
            log.error('Search root does not exist: %s', root)
            self.status.emit('Search root does not exist: {}'.format(root))
            return
        self.stop_scan(wait=True)
        self.folders = {}
        self.model.clear()
        self._sync_filter()
        skip = parse_skip_patterns(self.skip_dirs.text())
        self.worker = ScanWorker(root, self.threads.value(), skip, self.max_depth.value(), self)
        log.info('Searching %s for *.nk (%d threads%s, skip: %s, depth: %s)', root, self.worker.scanner.workers,
                 ' auto' if self.threads.value() == 0 else '', ';'.join(skip) or '-',
                 self.max_depth.value() or 'unlimited')
        self.worker.batch.connect(self._on_batch)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_done)
        self.worker.finished.connect(self.worker.deleteLater)
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.busy.emit(True)
        self.worker.start()

    def stop_scan(self, wait: bool = False) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            if wait:
                self.worker.wait()
        if wait:
            # signals of the old scan may still be queued; they are ignored by _stale()
            self.worker = None

    def _stale(self) -> bool:
        """True for queued signals of a previous (stopped) scan."""
        sender = self.sender()
        return sender is not None and sender is not self.worker

    def is_scanning(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def _on_batch(self, batch) -> None:
        if self._stale():
            return
        new_rows: List[ScriptEntry] = []
        for folder, entries in batch:
            self.folders[folder] = entries
            new_rows.extend(self.filter.filter_folder(entries))
        # sorting while rows stream in would make the table jump; it is re-enabled at the end
        self.table.setSortingEnabled(False)
        self.model.append(new_rows)

    def _on_progress(self, stats: ScanStats) -> None:
        if self._stale():
            return
        self.status.emit('Searching... {:,} folders listed, {:,} .nk files found, {} shown, {:.1f} s'.format(
            stats.folders, stats.files, self.model.rowCount(), stats.elapsed))

    def _on_done(self, stats: ScanStats) -> None:
        if self._stale():
            return
        self.last_stats = stats
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.busy.emit(False)
        self.table.setSortingEnabled(True)
        self.refilter()
        msg = '{} {:,} .nk files in {:,} folders in {:.1f} s{}.'.format(
            'Stopped after' if stats.stopped else 'Found', stats.files, stats.folders, stats.elapsed,
            ', {} folders could not be read'.format(stats.errors) if stats.errors else '')
        log.info('%s', msg)
        self.status.emit(msg + ' ' + self._counts_text())
        self.worker = None

    # ------------------------------------------------------------------ filtering
    def _sync_filter(self) -> bool:
        f = VersionFilter(
            name_patterns=self.search_for.text(), contains=self.search_contains.text(),
            version_regex=self.version_regex.text(),
            first_enabled=self.first_enabled.isChecked(), first_n=self.first_n.value(),
            last_enabled=self.last_enabled.isChecked(), last_n=self.last_n.value())
        ok = f.compile()
        self.regex_state.setText('' if ok else 'invalid')
        self.regex_state.setObjectName('ok' if ok else 'bad')
        self.regex_state.style().polish(self.regex_state)
        if ok:
            self.filter = f
        return ok

    def refilter(self) -> None:
        if not self._sync_filter():
            return
        rows: List[ScriptEntry] = []
        for folder in sorted(self.folders):
            rows.extend(self.filter.filter_folder(self.folders[folder]))
        self.model.set_entries(rows)
        if not self.is_scanning():
            self.status.emit(self._counts_text())

    # ------------------------------------------------------------------ marks / selection
    def _counts_text(self) -> str:
        total = sum(len(v) for v in self.folders.values())
        return '{:,} of {:,} scripts shown, {:,} marked.'.format(
            self.model.rowCount(), total, len(self.model.marked_entries()))

    def _update_counts(self) -> None:
        self.counts.setText('{:,} shown, {:,} marked'.format(self.model.rowCount(), len(self.model.marked_entries())))

    def mark_selected(self, value: Optional[bool]) -> None:
        rows = selected_rows(self.table)
        if rows:
            self.model.set_marks(rows, value)

    def send_marked(self) -> None:
        entries = self.model.marked_entries()
        if not entries:
            self.status.emit('Nothing marked.')
            return
        self.send_to_queue.emit(entries)

    def first_selected_path(self) -> str:
        row = first_selected_row(self.table)
        if row is not None and row < len(self.model.entries):
            return self.model.entries[row].path
        return ''

    def _double_clicked(self, index: QtCore.QModelIndex) -> None:
        if index.column() == 0:
            return
        row = self.proxy.mapToSource(index).row()
        reveal(self.model.entries[row].path)

    def _context_menu(self, pos) -> None:
        rows = selected_rows(self.table)
        menu = QtWidgets.QMenu(self)
        menu.addAction('Mark selected', lambda: self.mark_selected(True))
        menu.addAction('Unmark selected', lambda: self.mark_selected(False))
        menu.addAction('Toggle selected', lambda: self.mark_selected(None))
        menu.addSeparator()
        if rows:
            path = self.model.entries[rows[0]].path
            menu.addAction('Show in file browser', lambda: reveal(path))
            menu.addAction('Copy path(s)', lambda: QtWidgets.QApplication.clipboard().setText(
                '\n'.join(self.model.entries[r].path for r in rows)))
            menu.addAction('Send selected to Queue', lambda: self.send_to_queue.emit(
                [self.model.entries[r] for r in rows]))
        menu.exec(self.table.viewport().mapToGlobal(pos))
