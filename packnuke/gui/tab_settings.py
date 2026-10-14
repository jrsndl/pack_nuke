"""Settings tab: settings.json file handling, comfortable farm settings, raw JSON tree."""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from PySide6 import QtGui, QtWidgets

from ..core import settings as settings_mod
from .state import AppState
from .widgets import JsonTreeModel, PathEdit, button, hbox, hint, label, open_path, set_status_label, vbox

log = logging.getLogger('packnuke.gui')

EXE_FILTER = 'Executables (*.exe *.bat *.cmd);;All files (*)'


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._loading = False
        self._self_edit = False
        self._platform_edits: Dict[Tuple[str, str], PathEdit] = {}
        self._build()
        state.settings_loaded.connect(self.reload)
        state.dirty_changed.connect(self._update_dirty)
        state.settings_edited.connect(self._external_edit)

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        self.path = PathEdit('open', 'JSON (*.json);;All files (*)', 'path to settings.json')
        self.path.edit.returnPressed.connect(self.load)
        self.dirty_label = label('')
        file_row = hbox(label('Settings file:'), self.path, button('Load', self.load),
                        button('Save', self.save), button('Save as...', self.save_as),
                        button('Open in editor', lambda: open_path(self.state.settings_path)), self.dirty_label)

        # farm page
        farm = QtWidgets.QWidget()
        form = QtWidgets.QVBoxLayout(farm)
        for key, title, mode, flt in (
                ('nuke', 'Nuke executable', 'open', EXE_FILTER),
                ('deadline', 'Deadline command (deadlinecommand)', 'open', EXE_FILTER),
                ('deadline_python', 'pack_nuke.py as seen by the farm', 'open', 'Python (*.py);;All files (*)')):
            box = QtWidgets.QGroupBox(title)
            grid = QtWidgets.QGridLayout(box)
            for row, system in enumerate(settings_mod.PLATFORMS):
                pe = PathEdit(mode, flt)
                pe.changed.connect(lambda _t, k=key, s=system: self._platform_edited(k, s))
                self._platform_edits[(key, system)] = pe
                grid.addWidget(label(system + ':'), row, 0)
                grid.addWidget(pe, row, 1)
            grid.setColumnStretch(1, 1)
            form.addWidget(box)

        dl_box = QtWidgets.QGroupBox('Deadline job')
        dl = QtWidgets.QFormLayout(dl_box)
        self.pool = QtWidgets.QLineEdit()
        self.group = QtWidgets.QLineEdit()
        self.priority = QtWidgets.QSpinBox()
        self.priority.setRange(0, 100)
        self.department = QtWidgets.QLineEdit()
        self.limit_groups = QtWidgets.QLineEdit()
        self.limit_groups.setToolTip('Comma separated Deadline limit groups')
        self.comment = QtWidgets.QLineEdit()
        for w, name in ((self.pool, 'Pool:'), (self.group, 'Group:'), (self.priority, 'Priority:'),
                        (self.department, 'Department:'), (self.limit_groups, 'Limit groups:'),
                        (self.comment, 'Comment:')):
            dl.addRow(name, w)
        for w in (self.pool, self.group, self.department, self.limit_groups, self.comment):
            w.textEdited.connect(self._deadline_edited)
        self.priority.valueChanged.connect(self._deadline_edited)
        form.addWidget(dl_box)

        pk_box = QtWidgets.QGroupBox('Packing (farm side)')
        pk = QtWidgets.QFormLayout(pk_box)
        self.copy_threads = QtWidgets.QSpinBox()
        self.copy_threads.setRange(1, 64)
        self.copy_threads.setToolTip('Files copied in parallel by each farm job')
        self.skip_identical = QtWidgets.QCheckBox('Skip files already in the package (same size and date)')
        self.hashes = QtWidgets.QCheckBox('Generate file hashes (slower, helps later relinking)')
        self.category_first = QtWidgets.QCheckBox('Copy a file only into the first matching category')
        self.fail_missing = QtWidgets.QCheckBox('Fail the farm job when source files are missing')
        self.include_writes = QtWidgets.QCheckBox('Also pack files of Write nodes (existing renders)')
        self.mark_nodes = QtWidgets.QCheckBox('Colour relinked nodes in the packaged scripts')
        self.to_groups = QtWidgets.QCheckBox('Convert gizmos to groups in the packaged scripts')
        pk.addRow('Copy threads:', self.copy_threads)
        for w in (self.skip_identical, self.hashes, self.category_first, self.fail_missing, self.include_writes,
                  self.mark_nodes, self.to_groups):
            pk.addRow('', w)
            w.toggled.connect(self._packing_edited)
        self.copy_threads.valueChanged.connect(self._packing_edited)
        form.addWidget(pk_box)
        form.addStretch(1)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(farm)

        # raw json page
        self.json_model = JsonTreeModel(self)
        self.json_model.edited.connect(self._json_edited)
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.json_model)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 520)
        raw = QtWidgets.QWidget()
        raw.setLayout(vbox(
            hint('Every setting. Values keep their type (true/false, numbers). To add or remove '
                 'categories, use "Open in editor" and Load again.'),
            hbox(button('Expand all', self.tree.expandAll), button('Collapse all', self.tree.collapseAll), None),
            self.tree, margins=4))

        # validation page
        self.issues = QtWidgets.QListWidget()
        val = QtWidgets.QWidget()
        val.setLayout(vbox(hbox(button('Validate', self.validate), None), self.issues, margins=4))

        self.pages = QtWidgets.QTabWidget()
        self.pages.addTab(scroll, 'Farm')
        self.pages.addTab(raw, 'All settings (JSON)')
        self.pages.addTab(val, 'Validation')
        self.pages.currentChanged.connect(self._page_changed)
        self.setLayout(vbox(file_row, self.pages, margins=6))

    # ------------------------------------------------------------------ load / save
    def load(self) -> None:
        path = self.path.text()
        if self.state.dirty and path != self.state.settings_path:
            if QtWidgets.QMessageBox.question(self, 'Unsaved changes', 'Discard unsaved settings changes?') \
                    != QtWidgets.QMessageBox.Yes:
                return
        if self.state.load_settings(path):
            self.state.ini.set('settings_file', path)
            self.validate()

    def save(self) -> None:
        path = self.path.text() or self.state.settings_path
        if not path:
            self.save_as()
            return
        if path != self.state.settings_path and QtWidgets.QMessageBox.question(
                self, 'Save settings', 'Save the current settings to\n{}?'.format(path)) != QtWidgets.QMessageBox.Yes:
            return
        if self.state.save_settings(path):
            self.state.ini.set('settings_file', path)

    def save_as(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save settings as', self.state.settings_path,
                                                        'JSON (*.json)')
        if path:
            self.path.setText(path)
            if self.state.save_settings(path):
                self.state.ini.set('settings_file', path)

    def _update_dirty(self, dirty: bool) -> None:
        set_status_label(self.dirty_label, not dirty, 'unsaved changes' if dirty else 'saved')

    # ------------------------------------------------------------------ sync with state
    def reload(self) -> None:
        s = self.state.settings
        self._loading = True
        try:
            self.path.setText(self.state.settings_path)
            for (key, system), pe in self._platform_edits.items():
                pe.setText(settings_mod.platform_value(s.get(key) or {}, system))
            dj = s.get('deadline_job') or {}
            self.pool.setText(str(dj.get('pool', '')))
            self.group.setText(str(dj.get('group', '')))
            try:
                self.priority.setValue(int(dj.get('priority', 50)))
            except (TypeError, ValueError):
                self.priority.setValue(50)
            self.department.setText(str(dj.get('department', '')))
            self.limit_groups.setText(str(dj.get('LimitGroups', '')))
            self.comment.setText(str(dj.get('comment', '')))
            try:
                self.copy_threads.setValue(int(s['copy'].get('threads', 8)))
            except (TypeError, ValueError):
                self.copy_threads.setValue(8)
            self.skip_identical.setChecked(bool(s['copy'].get('skip_identical', True)))
            self.hashes.setChecked(bool(s['hashes'].get('hashes_generate')))
            self.category_first.setChecked(s['packing'].get('category_match') == 'first')
            self.fail_missing.setChecked(bool(s['packing'].get('fail_on_missing')))
            self.include_writes.setChecked(bool(s['packing'].get('include_write_nodes')))
            self.mark_nodes.setChecked(bool(s['packing'].get('mark_nodes', True)))
            self.to_groups.setChecked(bool(s['gizmos'].get('to_groups')))
            self.json_model.load(s)
        finally:
            self._loading = False
        self._update_dirty(self.state.dirty)

    def _commit(self, places: bool = False) -> None:
        self._self_edit = True
        try:
            self.state.edited(places=places)
        finally:
            self._self_edit = False

    def _external_edit(self) -> None:
        # places/anatomy edits elsewhere: keep the JSON tree in sync when it is visible
        if not self._self_edit and self.pages.currentIndex() == 1:
            self.json_model.load(self.state.settings)

    def _page_changed(self, index: int) -> None:
        if index == 1:
            self.json_model.load(self.state.settings)
        elif index == 2:
            self.validate()
        elif index == 0:
            self.reload()

    def _platform_edited(self, key: str, system: str) -> None:
        if self._loading:
            return
        self.state.settings.setdefault(key, {})[system] = self._platform_edits[(key, system)].text()
        self._commit()

    def _deadline_edited(self, *_args) -> None:
        if self._loading:
            return
        dj = self.state.settings.setdefault('deadline_job', {})
        dj.update({'pool': self.pool.text().strip(), 'group': self.group.text().strip(),
                   'priority': self.priority.value(), 'department': self.department.text().strip(),
                   'LimitGroups': self.limit_groups.text().strip(), 'comment': self.comment.text()})
        self._commit()

    def _packing_edited(self, *_args) -> None:
        if self._loading:
            return
        s = self.state.settings
        s['copy']['threads'] = self.copy_threads.value()
        s['copy']['skip_identical'] = self.skip_identical.isChecked()
        s['hashes']['hashes_generate'] = self.hashes.isChecked()
        s['packing']['category_match'] = 'first' if self.category_first.isChecked() else 'all'
        s['packing']['fail_on_missing'] = self.fail_missing.isChecked()
        s['packing']['include_write_nodes'] = self.include_writes.isChecked()
        s['packing']['mark_nodes'] = self.mark_nodes.isChecked()
        s['gizmos']['to_groups'] = self.to_groups.isChecked()
        self._commit()

    def _json_edited(self) -> None:
        data = self.json_model.to_python()
        if isinstance(data, dict):
            self.state.settings = settings_mod.complete(data)
            self._commit(places=True)

    def validate(self) -> None:
        self.issues.clear()
        issues = settings_mod.validate(self.state.settings)
        if not issues:
            self.issues.addItem('No problems found.')
        for level, msg in issues:
            it = QtWidgets.QListWidgetItem('{}: {}'.format(level.upper(), msg))
            it.setForeground(QtGui.QColor('#ff6b5a') if level == 'error' else QtGui.QColor('#ffa02f'))
            self.issues.addItem(it)
