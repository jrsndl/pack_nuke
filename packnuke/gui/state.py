"""Application state shared by all tabs: settings.json content, places, queue, ini file."""
from __future__ import annotations

import copy
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PySide6 import QtCore

from ..core import jobs, paths, settings as settings_mod, templates, tokens as tokens_mod
from ..core.versions import ScriptEntry

log = logging.getLogger('packnuke.gui')


@dataclass
class QueueEntry:
    path: str
    name: str
    folder: str
    version: str = ''
    marked: bool = True

    @property
    def key(self) -> str:
        return self.path.lower()

    @classmethod
    def from_script(cls, e: ScriptEntry) -> 'QueueEntry':
        return cls(path=e.path, name=e.name, folder=e.folder, version=e.version)


def to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Ini:
    """Thin typed wrapper around QSettings (INI file next to the app)."""

    def __init__(self, path: str):
        self.path = path
        self.qs = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
        self.qs.setFallbacksEnabled(False)

    def get(self, key: str, default: Any = '') -> Any:
        v = self.qs.value(key, default)
        return default if v is None else v

    def get_str(self, key: str, default: str = '') -> str:
        v = self.get(key, default)
        return str(v) if v is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        return to_bool(self.get(key, default), default)

    def get_int(self, key: str, default: int = 0) -> int:
        return to_int(self.get(key, default), default)

    def set(self, key: str, value: Any) -> None:
        if isinstance(value, bool):
            value = int(value)
        self.qs.setValue(key, value)

    def sync(self) -> None:
        self.qs.sync()


class AppState(QtCore.QObject):
    settings_loaded = QtCore.Signal()       # a different settings dict was loaded
    settings_edited = QtCore.Signal()       # something inside settings changed
    places_changed = QtCore.Signal()        # place list, anatomy or tags changed
    places_selected = QtCore.Signal()       # source/target place selection changed
    dirty_changed = QtCore.Signal(bool)
    queue_changed = QtCore.Signal()
    preview_changed = QtCore.Signal()       # the script used for previews may have changed
    timestamp_changed = QtCore.Signal()

    def __init__(self, app_dir: str, parent=None):
        super().__init__(parent)
        self.app_dir = paths.norm(app_dir)
        self.ini = Ini(self.app_dir + '/settings.ini')
        self.settings_path = ''
        self.settings: Dict[str, Any] = settings_mod.complete({})
        self._dirty = False
        self.place_source = ''
        self.place_target = ''
        self.timestamp = tokens_mod.timestamp()
        self.queue: List[QueueEntry] = []
        # the GUI tabs register callables returning the "first selected" script path
        self.preview_providers: List[Any] = []

    # ------------------------------------------------------------------ settings
    @property
    def dirty(self) -> bool:
        return self._dirty

    def set_dirty(self, dirty: bool = True) -> None:
        if dirty != self._dirty:
            self._dirty = dirty
            self.dirty_changed.emit(dirty)

    def edited(self, places: bool = False) -> None:
        """Call after changing ``self.settings`` in place."""
        self.set_dirty(True)
        self.settings_edited.emit()
        if places:
            self.places_changed.emit()

    def load_settings(self, path: str) -> bool:
        path = paths.norm(path)
        try:
            data = settings_mod.load_settings(path)
        except settings_mod.SettingsError as e:
            log.error('%s', e)
            return False
        self.settings = data
        self.settings_path = path
        self.set_dirty(False)
        self._fix_places()
        log.info('Loaded settings %s (%d places, %d categories)', path, len(data['places']),
                 len(data['categories']))
        for level, msg in settings_mod.validate(data):
            (log.error if level == 'error' else log.warning)('settings: %s', msg)
        self.settings_loaded.emit()
        self.places_changed.emit()
        return True

    def set_settings(self, data: Dict[str, Any], path: str = '', dirty: bool = True) -> None:
        self.settings = settings_mod.complete(data)
        if path:
            self.settings_path = paths.norm(path)
        self.set_dirty(dirty)
        self._fix_places()
        self.settings_loaded.emit()
        self.places_changed.emit()

    def save_settings(self, path: Optional[str] = None) -> bool:
        path = paths.norm(path or self.settings_path)
        if not path:
            log.error('No settings file path to save to.')
            return False
        try:
            settings_mod.save_settings(self.settings, path)
        except OSError as e:
            log.error('Saving settings to %s failed: %s', path, e)
            return False
        self.settings_path = path
        self.set_dirty(False)
        log.info('Saved settings to %s', path)
        return True

    # ------------------------------------------------------------------ places
    def place_names(self) -> List[str]:
        return list((self.settings.get('places') or {}).keys())

    def _fix_places(self) -> None:
        names = self.place_names()
        default_src = self.ini.get_str('place_source_default', '')
        if self.place_source not in names:
            self.place_source = default_src if default_src in names else (names[0] if names else '')
        if self.place_target not in names or self.place_target == self.place_source:
            others = [n for n in names if n != self.place_source]
            self.place_target = others[0] if others else ''

    def set_places(self, source: str, target: str) -> None:
        if (source, target) != (self.place_source, self.place_target):
            self.place_source, self.place_target = source, target
            self.places_selected.emit()

    def rename_place(self, old: str, new: str) -> None:
        places = self.settings['places']
        self.settings['places'] = {(new if k == old else k): v for k, v in places.items()}
        if self.place_source == old:
            self.place_source = new
        if self.place_target == old:
            self.place_target = new
        self.edited(places=True)

    # ------------------------------------------------------------------ tokens / job
    def refresh_timestamp(self) -> None:
        self.timestamp = tokens_mod.timestamp()
        self.timestamp_changed.emit()

    def base_tokens(self) -> Dict[str, Any]:
        return tokens_mod.place_tokens(self.settings, self.place_source, self.place_target, self.timestamp)

    def auto_job_name(self) -> str:
        return tokens_mod.job_name(self.settings, self.base_tokens())

    def auto_job_root(self) -> str:
        return tokens_mod.job_root(self.settings, self.base_tokens())

    def script_tags(self, script_path: str) -> Dict[str, str]:
        return tokens_mod.script_tags(self.settings, self.place_source, script_path)

    def script_tokens(self, script_path: str, job_folder: str = '', job_name: str = '') -> Dict[str, Any]:
        job_name = job_name or self.auto_job_name()
        job_folder = job_folder or templates.join_template(self.auto_job_root(), job_name)
        return tokens_mod.build_tokens(self.settings, self.place_source, self.place_target, script_path,
                                       self.timestamp, job_folder, job_name)

    def preview_script(self) -> str:
        for provider in self.preview_providers:
            p = provider()
            if p:
                return p
        return ''

    # ------------------------------------------------------------------ queue
    def add_to_queue(self, entries: List[ScriptEntry]) -> int:
        known = {q.key for q in self.queue}
        added = 0
        for e in entries:
            if e.key not in known:
                self.queue.append(QueueEntry.from_script(e))
                known.add(e.key)
                added += 1
        if added:
            self.queue_changed.emit()
        return added

    def build_job(self, job_folder: str, job_name: str) -> jobs.Job:
        job = jobs.Job(job_name=job_name, job_path=paths.norm(job_folder), timestamp=self.timestamp,
                       place_source=self.place_source, place_target=self.place_target)
        for q in [q for q in self.queue if q.marked]:
            sid = jobs.make_script_id(len(job.scripts), q.name)
            job.scripts.append(jobs.JobScript(
                id=sid, path=q.path, name=q.name, version=q.version,
                tags=self.script_tags(q.path),
                tokens=self.script_tokens(q.path, job_folder, job_name)))
        return job

    def settings_copy(self) -> Dict[str, Any]:
        return copy.deepcopy(self.settings)

    def presets_folder(self) -> str:
        folder = self.ini.get_str('presets_folder', '')
        if not folder:
            folder = self.app_dir + '/presets'
        return paths.norm(folder)

    def ensure_dir(self, folder: str) -> bool:
        try:
            os.makedirs(folder, exist_ok=True)
            return True
        except OSError as e:
            log.error('Cannot create folder %s: %s', folder, e)
            return False
