"""Presets tab: named snapshots of the GUI state (search, filters, places, settings file),
stored as JSON files in the presets folder configured in settings.ini."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Callable, Dict, List

from PySide6 import QtCore, QtWidgets

from ..core import paths, settings as settings_mod
from .state import AppState
from . import help as help_texts
from .widgets import PathEdit, button, hbox, hint, label, open_path, vbox

log = logging.getLogger('packnuke.gui')

PRESET_EXT = '.json'
PRESET_KIND = 'packnuke_preset'


def preset_file_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip() + PRESET_EXT


class PresetsTab(QtWidgets.QWidget):
    def __init__(self, state: AppState, get_gui: Callable[[], Dict[str, Any]],
                 set_gui: Callable[[Dict[str, Any]], None], parent=None):
        super().__init__(parent)
        self.state = state
        self.get_gui = get_gui
        self.set_gui = set_gui
        self._build()
        state.places_changed.connect(self._fill_default_place)
        state.settings_loaded.connect(self._fill_default_place)

    def _build(self) -> None:
        self.folder = PathEdit('dir')
        self.folder.setText(self.state.presets_folder())
        self.folder.edit.editingFinished.connect(self._folder_changed)
        self.folder.btn.clicked.connect(self._folder_changed)

        self.list = QtWidgets.QListWidget()
        self.list.currentTextChanged.connect(self._selected)
        self.list.itemDoubleClicked.connect(lambda _i: self.load_selected())
        self.details = QtWidgets.QPlainTextEdit()
        self.details.setReadOnly(True)

        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText('preset name')
        self.name.returnPressed.connect(self.save)
        self.embed = QtWidgets.QCheckBox('Store the full settings.json content in the preset')
        self.embed.setToolTip('Off: the preset remembers the settings file path only.\n'
                              'On: the preset carries its own copy of the settings (incl. unsaved edits).')

        self.default_place = QtWidgets.QComboBox()
        self.default_place.setEditable(True)
        self.default_place.setToolTip('Source place selected when a settings file is loaded')
        self.default_place.currentTextChanged.connect(
            lambda t: self.state.ini.set('place_source_default', t.strip()))

        left = QtWidgets.QWidget()
        left.setLayout(vbox(
            label('Presets'), self.list,
            hbox(button('Load', self.load_selected), button('Delete', self.delete_selected),
                 button('Refresh', self.refresh))))
        right = QtWidgets.QWidget()
        right.setLayout(vbox(label('Preset content'), self.details))
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([300, 600])

        save_box = QtWidgets.QGroupBox('Save current state as preset')
        save_box.setLayout(vbox(
            hbox(label('Name:'), self.name, button('Save preset', self.save, object_name='primary')),
            self.embed,
            hint('A preset stores: search root, skip folders, depth, filters, version regex, first/last N, '
                 'source/target place and the settings file.'), margins=6))

        help_texts.apply([
            (self.folder, 'Presets folder:'), (self.folder.edit, 'Presets folder:'), (self.list, 'Presets'),
            (self.details, 'Preset content'), (self.name, 'Name:'), (self.default_place, 'Default source place:')])
        self.setLayout(vbox(
            hbox(label('Presets folder:'), self.folder, button('Open', lambda: open_path(self.folder.text()))),
            hint('The folder is stored in settings.ini (presets_folder). Share it between artists to share presets.'),
            split, save_box,
            hbox(label('Default source place:'), self.default_place, None), margins=6))
        self.refresh()

    # ------------------------------------------------------------------ folder / list
    def _folder_changed(self) -> None:
        folder = paths.norm(self.folder.text())
        if folder and folder != self.state.ini.get_str('presets_folder', ''):
            self.state.ini.set('presets_folder', folder)
            log.info('Presets folder: %s', folder)
        self.refresh()

    def folder_path(self) -> str:
        return paths.norm(self.folder.text()) or self.state.presets_folder()

    def refresh(self) -> None:
        folder = self.folder_path()
        cur = self.list.currentItem().text() if self.list.currentItem() else ''
        self.list.clear()
        if not os.path.isdir(folder):
            self.details.setPlainText('Presets folder does not exist yet; it is created on the first save.')
            return
        names = sorted((n[:-len(PRESET_EXT)] for n in os.listdir(folder) if n.lower().endswith(PRESET_EXT)),
                       key=str.lower)
        self.list.addItems(names)
        if cur in names:
            self.list.setCurrentRow(names.index(cur))

    def _fill_default_place(self) -> None:
        cur = self.state.ini.get_str('place_source_default', '')
        self.default_place.blockSignals(True)
        self.default_place.clear()
        self.default_place.addItems(self.state.place_names())
        self.default_place.setCurrentText(cur)
        self.default_place.blockSignals(False)

    def _path(self, name: str) -> str:
        return self.folder_path() + '/' + preset_file_name(name)

    def _read(self, name: str) -> Dict[str, Any]:
        with open(self._path(name), 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError('not a preset')
        return data

    def _selected(self, name: str) -> None:
        if not name:
            self.details.clear()
            return
        self.name.setText(name)
        try:
            data = self._read(name)
        except (OSError, ValueError) as e:
            self.details.setPlainText('Cannot read preset: {}'.format(e))
            return
        shown = dict(data)
        if 'settings' in shown:
            shown['settings'] = '<embedded settings.json, {} places, {} categories>'.format(
                len((data['settings'] or {}).get('places') or {}), len((data['settings'] or {}).get('categories') or {}))
        self.details.setPlainText(json.dumps(shown, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------------ save / load / delete
    def save(self) -> None:
        name = self.name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, 'Save preset', 'Enter a preset name.')
            return
        folder = self.folder_path()
        if not self.state.ensure_dir(folder):
            return
        path = self._path(name)
        if os.path.exists(path) and QtWidgets.QMessageBox.question(
                self, 'Save preset', 'Preset "{}" exists. Overwrite?'.format(name)) != QtWidgets.QMessageBox.Yes:
            return
        data: Dict[str, Any] = {
            'kind': PRESET_KIND,
            'name': name,
            'saved': time.strftime('%Y-%m-%d %H:%M:%S'),
            'settings_file': self.state.settings_path,
            'gui': self.get_gui(),
        }
        if self.embed.isChecked():
            data['settings'] = self.state.settings_copy()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            log.error('Saving preset %s failed: %s', path, e)
            return
        log.info('Preset "%s" saved to %s', name, path)
        self.refresh()
        items = self.list.findItems(name, QtCore.Qt.MatchExactly)
        if items:
            self.list.setCurrentItem(items[0])

    def load_selected(self) -> None:
        item = self.list.currentItem()
        if item:
            self.load(item.text())

    def load(self, name: str) -> bool:
        try:
            data = self._read(name)
        except (OSError, ValueError) as e:
            log.error('Cannot read preset %s: %s', name, e)
            return False
        if self.state.dirty and QtWidgets.QMessageBox.question(
                self, 'Load preset', 'Settings have unsaved changes. Load the preset anyway?') \
                != QtWidgets.QMessageBox.Yes:
            return False
        settings_file = data.get('settings_file') or ''
        if isinstance(data.get('settings'), dict):
            on_disk = None
            if settings_file and os.path.isfile(settings_file):
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        on_disk = json.load(f)
                except (OSError, ValueError):
                    on_disk = None
            same = isinstance(on_disk, dict) and \
                settings_mod.complete(on_disk) == settings_mod.complete(data['settings'])
            self.state.set_settings(data['settings'], settings_file, dirty=not same)
            log.info('Preset "%s": using embedded settings%s', name,
                     '' if same else ' (differs from the file on disk - not saved yet)')
        elif settings_file:
            if not self.state.load_settings(settings_file):
                log.error('Preset "%s": settings file could not be loaded: %s', name, settings_file)
        self.set_gui(data.get('gui') or {})
        self.state.ini.set('last_preset', name)
        log.info('Preset "%s" loaded.', name)
        return True

    def delete_selected(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        name = item.text()
        if QtWidgets.QMessageBox.question(self, 'Delete preset', 'Delete preset "{}"?'.format(name)) \
                != QtWidgets.QMessageBox.Yes:
            return
        try:
            os.remove(self._path(name))
            log.info('Preset "%s" deleted.', name)
        except OSError as e:
            log.error('Deleting preset %s failed: %s', name, e)
        self.refresh()

    def preset_names(self) -> List[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]
