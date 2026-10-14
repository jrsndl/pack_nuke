"""Main window: tabs, status bar, ini persistence."""
from __future__ import annotations

import logging
from typing import Any, Dict

from PySide6 import QtCore, QtGui, QtWidgets

from .. import __version__
from . import help as help_texts
from .state import AppState
from .widgets import bold_group_titles
from .tab_log import LogTab, QtLogHandler
from .tab_places import PlacesTab
from .tab_presets import PresetsTab
from .tab_queue import QueueTab
from .tab_scripts import ScriptsTab
from .tab_settings import SettingsTab

log = logging.getLogger('packnuke.gui')

GUI_KEYS = ('search_root', 'skip_dirs', 'max_depth', 'scan_threads', 'search_for', 'search_contains',
            'search_version_regex', 'versions_get_first', 'versions_first', 'versions_get_last',
            'versions_last', 'place_source', 'place_target', 'inspector')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app_dir: str, log_handler: QtLogHandler, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Pack Nuke {}'.format(__version__))
        self.setWindowIcon(QtGui.QIcon(':/images/folder.png'))
        self.resize(1400, 900)
        self.state = AppState(app_dir, self)

        self.log_tab = LogTab(log_handler)
        self.scripts = ScriptsTab()
        self.queue = QueueTab(self.state)
        self.places = PlacesTab(self.state)
        self.settings_tab = SettingsTab(self.state)
        self.presets = PresetsTab(self.state, self.gui_state, self.set_gui_state)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.scripts, 'Get Nuke Scripts')
        self.tabs.addTab(self.queue, 'Queue')
        self.tabs.addTab(self.places, 'Places')
        self.tabs.addTab(self.settings_tab, 'Settings')
        self.tabs.addTab(self.presets, 'Presets')
        self.tabs.addTab(self.log_tab, 'Log')
        for i in range(self.tabs.count()):
            self.tabs.setTabToolTip(i, help_texts.tip('tab:' + self.tabs.tabText(i)))
        self.setCentralWidget(self.tabs)

        # status bar
        self.status_label = QtWidgets.QLabel('')
        self.busy_bar = QtWidgets.QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setMaximumWidth(160)
        self.busy_bar.setMaximumHeight(14)
        self.busy_bar.setVisible(False)
        self.busy_bar.setToolTip('Working (search, submission or local run)')
        self.settings_label = QtWidgets.QLabel('')
        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addPermanentWidget(self.settings_label)
        self.statusBar().addPermanentWidget(self.busy_bar)
        self._busy = 0

        # wiring
        for tab in (self.scripts, self.queue):
            tab.status.connect(self.show_status)
            tab.busy.connect(self.set_busy)
        self.scripts.send_to_queue.connect(self.add_to_queue)
        self.scripts.selection_changed.connect(self._preview_source_changed)
        self.queue.selection_changed.connect(self._preview_source_changed)
        self.state.queue_changed.connect(self._update_queue_title)
        self.queue.model.marks_changed.connect(self._update_queue_title)
        self.state.dirty_changed.connect(self._update_settings_label)
        self.state.settings_loaded.connect(self._update_settings_label)
        self.log_tab.error_logged.connect(lambda msg: self.show_status('Error: ' + msg.splitlines()[0]))
        self.state.preview_providers.append(self._preview_path)

        bold_group_titles(self)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+S'), self, activated=self.settings_tab.save)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+.'), self, activated=self.scripts.stop_scan)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+F'), self, activated=self._focus_search)

        self.restore()
        log.info('Pack Nuke %s started. Settings ini: %s', __version__, self.state.ini.path)

    # ------------------------------------------------------------------ status
    def show_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_busy(self, busy: bool) -> None:
        self._busy = max(0, self._busy + (1 if busy else -1))
        self.busy_bar.setVisible(self._busy > 0)

    def _update_settings_label(self, *_args) -> None:
        st = self.state
        if st.settings_source == 'preset':
            text = 'Preset: {}'.format(st.preset_name)
        else:
            text = st.settings_path or 'no settings file'
        self.settings_label.setText('{}{}'.format(text, '  (unsaved)' if st.dirty else ''))
        self.settings_label.setToolTip('Settings come from: {}'.format(st.settings_path or '-'))

    def _update_queue_title(self) -> None:
        n = len(self.state.queue)
        marked = sum(1 for q in self.state.queue if q.marked)
        self.tabs.setTabText(1, 'Queue ({}/{})'.format(marked, n) if n else 'Queue')

    def _focus_search(self) -> None:
        self.tabs.setCurrentWidget(self.scripts)
        self.scripts.root.edit.setFocus()

    # ------------------------------------------------------------------ queue / preview
    def add_to_queue(self, entries) -> None:
        added = self.state.add_to_queue(entries)
        msg = 'Added {} script(s) to the queue{}.'.format(
            added, ', {} were already there'.format(len(entries) - added) if added < len(entries) else '')
        log.info('%s', msg)
        self.show_status(msg)
        self.state.preview_changed.emit()

    def _preview_path(self) -> str:
        """First selected queue item; if the queue is empty, first selected found script."""
        if self.state.queue:
            return self.queue.first_path()
        p = self.scripts.first_selected_path()
        if p:
            return p
        entries = self.scripts.model.entries
        if entries:
            idx = self.scripts.proxy.mapToSource(self.scripts.proxy.index(0, 0))
            return entries[idx.row()].path if idx.isValid() else entries[0].path
        return ''

    def _preview_source_changed(self) -> None:
        self.state.preview_changed.emit()

    # ------------------------------------------------------------------ gui state (presets + ini)
    def gui_state(self) -> Dict[str, Any]:
        s = {}
        s.update(self.scripts.get_state())
        s.update(self.queue.get_state())
        return s

    def set_gui_state(self, s: Dict[str, Any]) -> None:
        self.scripts.set_state(s)
        self.queue.set_state(s)

    def restore(self) -> None:
        ini = self.state.ini
        geo = ini.get('geometry', None)
        if isinstance(geo, (QtCore.QByteArray, bytes)):
            self.restoreGeometry(geo)
        stored = {k: ini.get(k) for k in GUI_KEYS if ini.qs.contains(k)}
        last_preset = ini.get_str('last_preset', '')
        if last_preset and last_preset in self.presets.preset_names() and self.presets.load(last_preset):
            log.info('Restored last preset "%s".', last_preset)
        else:
            default = self.state.app_dir + '/settings.json'
            if not self.state.load_settings(default):
                log.warning('No settings loaded - choose a preset or a settings file.')
        self.set_gui_state(stored)   # last session's search/filters win over the preset's
        self.settings_tab.reload()
        self.places.reload()
        self.log_tab.level_combo.setCurrentIndex(ini.get_int('log_level', 1))
        self.tabs.setCurrentIndex(ini.get_int('last_tab', 0))
        self._update_settings_label()

    def save_ini(self) -> None:
        ini = self.state.ini
        for k, v in self.gui_state().items():
            ini.set(k, v)
        ini.set('presets_folder', self.presets.folder_path())
        ini.set('log_level', self.log_tab.level_combo.currentIndex())
        ini.set('last_tab', self.tabs.currentIndex())
        ini.set('geometry', self.saveGeometry())
        ini.sync()

    def closeEvent(self, event) -> None:
        if self.state.dirty:
            res = QtWidgets.QMessageBox.question(
                self, 'Unsaved settings', 'Settings have unsaved changes. Save them before closing?',
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Save)
            if res == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
            if res == QtWidgets.QMessageBox.Save and not self.state.save_settings():
                event.ignore()
                return
        self.scripts.stop_scan(wait=True)
        self.queue.shutdown()
        self.save_ini()
        event.accept()
